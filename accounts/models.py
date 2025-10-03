# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import EmailValidator
import uuid
import string
import random
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import datetime


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True, validators=[EmailValidator()])
    is_student = models.BooleanField(default=False)
    university = models.CharField(max_length=200, blank=True)
    student_id = models.CharField(max_length=50, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    # Like/Dislike Bank (what users can spend)
    likes_balance = models.IntegerField(default=0)
    super_likes_balance = models.IntegerField(default=0)
    unlikes_balance = models.IntegerField(default=0)
    
    # Received counts (what others gave them)
    received_likes_count = models.IntegerField(default=0)
    received_super_likes_count = models.IntegerField(default=0)
    received_unlikes_count = models.IntegerField(default=0)
    
    points_balance = models.IntegerField(default=0)

    # Referral system fields
    referral_code = models.CharField(max_length=10, unique=True, blank=True)
    referred_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')
    referral_points_earned = models.IntegerField(default=0)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()
        super().save(*args, **kwargs)

    def generate_referral_code(self):
        """Generate a unique referral code"""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not CustomUser.objects.filter(referral_code=code).exists():
                return code

    def get_referral_count(self):
        """Get the number of successful referrals"""
        return self.referrals.count()

    def get_referral_points(self):
        """Get total points earned from referrals"""
        return self.referral_points_earned

class Referral(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    referrer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='referral_activities')
    referred_user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='referral_record')
    points_awarded = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['referrer', 'referred_user']

    def __str__(self):
        return f"{self.referrer.username} referred {self.referred_user.username}"

# Signal to award referral points when a referred user completes their profile
@receiver(post_save, sender='profiles.Profile')
def award_referral_points(sender, instance, created, **kwargs):
    """Award points to referrer when referred user completes their profile"""
    if instance.is_complete and instance.user.referred_by:
        # Check if referral record exists and is still pending
        try:
            referral = Referral.objects.get(
                referrer=instance.user.referred_by,
                referred_user=instance.user,
                status='pending'
            )

            # Award points to referrer
            points_to_award = 50  # 50 points for successful referral
            referral.referrer.points_balance += points_to_award
            referral.referrer.referral_points_earned += points_to_award
            referral.referrer.save()

            # Update referral record
            referral.points_awarded = points_to_award
            referral.status = 'completed'
            referral.completed_at = datetime.now()
            referral.save()

        except Referral.DoesNotExist:
            # Create referral record if it doesn't exist
            if instance.user.referred_by:
                points_to_award = 50
                instance.user.referred_by.points_balance += points_to_award
                instance.user.referred_by.referral_points_earned += points_to_award
                instance.user.referred_by.save()

                Referral.objects.create(
                    referrer=instance.user.referred_by,
                    referred_user=instance.user,
                    points_awarded=points_to_award,
                    status='completed',
                    completed_at=datetime.now()
                )
    
    def clean(self):
        super().clean()
        # Validate student email
        if self.email and self.is_student:
            student_domains = ['.edu', '.ac.', 'student.', '.uni-']
            if not any(domain in self.email.lower() for domain in student_domains):
                from django.core.exceptions import ValidationError
                raise ValidationError('Please use a valid student email address.')
    
    def save(self, *args, **kwargs):
        # Auto-detect if email is from educational institution
        if self.email:
            student_domains = ['.edu', '.ac.', 'student.', '.uni-']
            self.is_student = any(domain in self.email.lower() for domain in student_domains)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.email