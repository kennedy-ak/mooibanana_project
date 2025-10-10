# profiles/models.py
from django.db import models
from django.contrib.auth import get_user_model
from PIL import Image
import os

User = get_user_model()

class Profile(models.Model):
    STUDY_CHOICES = [
        ('computer_science', 'Computer Science'),
        ('business', 'Business'),
        ('engineering', 'Engineering'),
        ('medicine', 'Medicine'),
        ('law', 'Law'),
        ('arts', 'Arts'),
        ('psychology', 'Psychology'),
        ('other', 'Other'),
    ]

    YEAR_CHOICES = [
        (1, 'First Year'),
        (2, 'Second Year'),
        (3, 'Third Year'),
        (4, 'Fourth Year'),
        (5, 'Fifth Year'),
        (6, 'Graduate'),
    ]

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('non_binary', 'Non-Binary'),
        ('prefer_not_to_say', 'Prefer not to say'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)
    study_field = models.CharField(max_length=20, choices=STUDY_CHOICES, blank=True)
    study_year = models.IntegerField(choices=YEAR_CHOICES, null=True, blank=True)
    school_name = models.CharField(max_length=200, blank=True, help_text="Name of your school/university")
    interests = models.TextField(blank=True, help_text="Comma-separated interests")
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True)
    city = models.CharField(max_length=100, blank=True, help_text="Your city")
    location = models.CharField(max_length=100, blank=True, help_text="General location/region")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="Latitude for location-based matching")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="Longitude for location-based matching")
    is_complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['is_complete']),
            models.Index(fields=['study_field']),
            models.Index(fields=['school_name']),
            models.Index(fields=['city']),
            models.Index(fields=['location']),
            models.Index(fields=['birth_date']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Resize image (only for local storage, Cloudinary handles this via transformations)
        if self.profile_picture:
            try:
                img = Image.open(self.profile_picture.path)
                if img.height > 300 or img.width > 300:
                    output_size = (300, 300)
                    img.thumbnail(output_size)
                    img.save(self.profile_picture.path)
            except (NotImplementedError, AttributeError):
                # Cloudinary storage doesn't support .path, skip resize
                pass
        
        # Check if profile is complete
        self.is_complete = bool(
            self.bio and self.study_field and self.study_year and 
            self.interests and self.profile_picture
        )
        if self.is_complete != Profile.objects.filter(pk=self.pk).first().is_complete:
            Profile.objects.filter(pk=self.pk).update(is_complete=self.is_complete)
    
    def get_interests_list(self):
        return [interest.strip() for interest in self.interests.split(',') if interest.strip()]

    def calculate_distance_to(self, other_profile):
        """Calculate distance in kilometers to another profile using Haversine formula"""
        if not all([self.latitude, self.longitude, other_profile.latitude, other_profile.longitude]):
            return None

        import math

        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [
            float(self.latitude), float(self.longitude),
            float(other_profile.latitude), float(other_profile.longitude)
        ])

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))

        # Radius of earth in kilometers
        r = 6371

        return c * r
    
    @property
    def age(self):
        if self.birth_date:
            from datetime import date
            today = date.today()
            return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        return None

    def get_primary_photo(self):
        """Get the primary photo (profile_picture or first uploaded photo)"""
        if self.profile_picture:
            return self.profile_picture.url
        first_photo = self.photos.first()
        if first_photo:
            return first_photo.image.url
        return None

    def get_all_photos(self):
        """Get all photos including profile_picture and additional photos"""
        photos = []
        if self.profile_picture:
            photos.append({'url': self.profile_picture.url, 'is_primary': True})
        for photo in self.photos.all():
            photos.append({'url': photo.image.url, 'is_primary': False})
        return photos

class ProfilePhoto(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='profile_photos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'uploaded_at']

    def __str__(self):
        return f"{self.profile.user.username} - Photo {self.id}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Resize image (only for local storage, Cloudinary handles this via transformations)
        if self.image:
            try:
                img = Image.open(self.image.path)
                if img.height > 800 or img.width > 800:
                    output_size = (800, 800)
                    img.thumbnail(output_size)
                    img.save(self.image.path)
            except (NotImplementedError, AttributeError):
                # Cloudinary storage doesn't support .path, skip resize
                pass

    def delete(self, *args, **kwargs):
        # Delete the image file (works for both local and Cloudinary)
        if self.image:
            try:
                # For Cloudinary storage, use storage delete
                self.image.delete(save=False)
            except (NotImplementedError, AttributeError, FileNotFoundError):
                # If deletion fails, skip
                pass
        super().delete(*args, **kwargs)