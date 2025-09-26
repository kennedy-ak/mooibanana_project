from django.db import models
from django.core.validators import URLValidator


class Advertisement(models.Model):
    brand_name = models.CharField(max_length=100)
    flyer_image = models.ImageField(upload_to='advertisements/')
    brand_url = models.URLField(blank=True, null=True, validators=[URLValidator()])
    is_active = models.BooleanField(default=True)
    display_priority = models.PositiveIntegerField(default=1, help_text="Higher numbers display first")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-display_priority', '-created_at']
        verbose_name = "Advertisement"
        verbose_name_plural = "Advertisements"

    def __str__(self):
        return f"{self.brand_name} - {'Active' if self.is_active else 'Inactive'}"