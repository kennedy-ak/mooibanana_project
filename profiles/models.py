# profiles/models.py
from django.db import models
from django.contrib.auth import get_user_model
from PIL import Image

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
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    study_field = models.CharField(max_length=20, choices=STUDY_CHOICES, blank=True)
    study_year = models.IntegerField(choices=YEAR_CHOICES, null=True, blank=True)
    interests = models.TextField(blank=True, help_text="Comma-separated interests")
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True)
    location = models.CharField(max_length=100, blank=True)
    is_complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Resize image
        if self.profile_picture:
            img = Image.open(self.profile_picture.path)
            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(self.profile_picture.path)
        
        # Check if profile is complete
        self.is_complete = bool(
            self.bio and self.study_field and self.study_year and 
            self.interests and self.profile_picture
        )
        if self.is_complete != Profile.objects.filter(pk=self.pk).first().is_complete:
            Profile.objects.filter(pk=self.pk).update(is_complete=self.is_complete)
    
    def get_interests_list(self):
        return [interest.strip() for interest in self.interests.split(',') if interest.strip()]
    
    @property
    def age(self):
        if self.birth_date:
            from datetime import date
            today = date.today()
            return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        return None

class ProfilePhoto(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='profile_photos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Resize image
        img = Image.open(self.image.path)
        if img.height > 800 or img.width > 800:
            output_size = (800, 800)
            img.thumbnail(output_size)
            img.save(self.image.path)