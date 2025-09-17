
# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'is_student', 'university', 'likes_balance', 'points_balance', 'is_verified']
    list_filter = ['is_student', 'is_verified', 'university']
    fieldsets = UserAdmin.fieldsets + (
        ('Student Info', {'fields': ('is_student', 'university', 'student_id', 'is_verified')}),
        ('Balances', {'fields': ('likes_balance', 'points_balance')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)
