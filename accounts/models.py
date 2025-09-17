# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import EmailValidator


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True, validators=[EmailValidator()])
    is_student = models.BooleanField(default=False)
    university = models.CharField(max_length=200, blank=True)
    student_id = models.CharField(max_length=50, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    likes_balance = models.IntegerField(default=0)
    super_likes_balance = models.IntegerField(default=0)
    points_balance = models.IntegerField(default=0)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
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