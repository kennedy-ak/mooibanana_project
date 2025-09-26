from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class TextUpdate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='text_updates')
    content = models.TextField(max_length=280, help_text="Share what's on your mind (max 280 characters)")
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    # Optional styling fields
    background_color = models.CharField(max_length=7, default='#007bff', help_text="Hex color code")
    text_color = models.CharField(max_length=7, default='#ffffff', help_text="Hex color code")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.username}: {self.content[:50]}..."
    
    @property
    def is_recent(self):
        """Check if update is within the last 24 hours"""
        return self.created_at >= timezone.now() - timedelta(hours=24)
    
    @property 
    def time_ago(self):
        """Get human-readable time since posted"""
        diff = timezone.now() - self.created_at
        
        if diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours}h ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes}m ago"
        else:
            return "Just now"
    
    def save(self, *args, **kwargs):
        # Auto-deactivate updates older than 7 days
        if self.created_at and self.created_at < timezone.now() - timedelta(days=7):
            self.is_active = False
        super().save(*args, **kwargs)