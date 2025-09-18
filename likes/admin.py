
# likes/admin.py
from django.contrib import admin
from .models import Like, Unlike

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['from_user', 'to_user', 'like_type', 'is_mutual', 'created_at']
    list_filter = ['like_type', 'is_mutual', 'created_at']
    search_fields = ['from_user__username', 'to_user__username']
    readonly_fields = ['created_at']

@admin.register(Unlike)
class UnlikeAdmin(admin.ModelAdmin):
    list_display = ['from_user', 'to_user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['from_user__username', 'to_user__username']
    readonly_fields = ['created_at']