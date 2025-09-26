from django.contrib import admin
from .models import Advertisement


@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ['brand_name', 'is_active', 'display_priority', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['brand_name']
    list_editable = ['is_active', 'display_priority']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-display_priority', '-created_at']
    
    fieldsets = (
        ('Brand Information', {
            'fields': ('brand_name', 'flyer_image', 'brand_url')
        }),
        ('Display Settings', {
            'fields': ('is_active', 'display_priority')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )