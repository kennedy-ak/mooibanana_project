from django.contrib import admin
from .models import TextUpdate

@admin.register(TextUpdate)
class TextUpdateAdmin(admin.ModelAdmin):
    list_display = ['user', 'content_preview', 'created_at', 'is_active', 'is_recent']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__username', 'content']
    readonly_fields = ['created_at']
    list_per_page = 50
    
    def content_preview(self, obj):
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content
    content_preview.short_description = "Content Preview"
    
    def is_recent(self, obj):
        return obj.is_recent
    is_recent.boolean = True
    is_recent.short_description = "Recent (24h)"