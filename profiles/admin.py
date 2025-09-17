
# profiles/admin.py
from django.contrib import admin
from .models import Profile, ProfilePhoto

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'study_field', 'study_year', 'is_complete', 'created_at']
    list_filter = ['study_field', 'study_year', 'is_complete']
    search_fields = ['user__username', 'user__email', 'bio']

@admin.register(ProfilePhoto)
class ProfilePhotoAdmin(admin.ModelAdmin):
    list_display = ['profile', 'uploaded_at']
    list_filter = ['uploaded_at']
