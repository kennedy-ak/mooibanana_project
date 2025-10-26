from django.db import models
from django.core.validators import URLValidator
from django.core.cache import cache


class Advertisement(models.Model):
    brand_name = models.CharField(max_length=100)
    description = models.CharField(max_length=200, blank=True, help_text="Short description to display with the ad")
    flyer_image = models.ImageField(upload_to='advertisements/')
    brand_url = models.URLField(blank=True, null=True, validators=[URLValidator()], help_text="Website URL (optional)")
    is_active = models.BooleanField(default=True)
    display_priority = models.PositiveIntegerField(default=1, help_text="Higher numbers display first")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-display_priority', '-created_at']
        verbose_name = "Advertisement"
        verbose_name_plural = "Advertisements"
        indexes = [
            models.Index(fields=['-display_priority', '-created_at']),
            models.Index(fields=['is_active', '-display_priority']),
        ]

    def __str__(self):
        return f"{self.brand_name} - {'Active' if self.is_active else 'Inactive'}"

    @classmethod
    def get_active_ads(cls, limit=3):
        """Get active advertisements with caching"""
        cache_key = f'active_advertisements_{limit}'
        ads = cache.get(cache_key)

        if ads is None:
            ads = list(cls.objects.filter(is_active=True).order_by('-display_priority')[:limit])
            # Cache for 30 minutes
            cache.set(cache_key, ads, 60 * 30)

        return ads

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Clear cache when advertisement is saved
        self._clear_ad_cache()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        # Clear cache when advertisement is deleted
        self._clear_ad_cache()

    @staticmethod
    def _clear_ad_cache():
        """Clear all advertisement caches"""
        for i in range(1, 10):  # Clear cache for limits 1-10
            cache.delete(f'active_advertisements_{i}')