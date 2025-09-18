
# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count
from .models import CustomUser, Referral

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'is_student', 'university', 'likes_balance', 'points_balance', 'likes_given_count', 'likes_received_count', 'unlikes_given_count', 'unlikes_received_count', 'referral_code', 'is_verified']
    list_filter = ['is_student', 'is_verified', 'university']
    fieldsets = UserAdmin.fieldsets + (
        ('Student Info', {'fields': ('is_student', 'university', 'student_id', 'is_verified')}),
        ('Balances', {'fields': ('likes_balance', 'super_likes_balance', 'points_balance')}),
        ('Referral Info', {'fields': ('referral_code', 'referred_by', 'referral_points_earned')}),
    )
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            likes_given_count=Count('likes_given'),
            likes_received_count=Count('likes_received'),
            unlikes_given_count=Count('unlikes_given'),
            unlikes_received_count=Count('unlikes_received')
        )
        return queryset
    
    def likes_given_count(self, obj):
        return obj.likes_given_count
    likes_given_count.short_description = 'Likes Given'
    likes_given_count.admin_order_field = 'likes_given_count'
    
    def likes_received_count(self, obj):
        return obj.likes_received_count
    likes_received_count.short_description = 'Likes Received'
    likes_received_count.admin_order_field = 'likes_received_count'
    
    def unlikes_given_count(self, obj):
        return obj.unlikes_given_count
    unlikes_given_count.short_description = 'Unlikes Given'
    unlikes_given_count.admin_order_field = 'unlikes_given_count'
    
    def unlikes_received_count(self, obj):
        return obj.unlikes_received_count
    unlikes_received_count.short_description = 'Unlikes Received'
    unlikes_received_count.admin_order_field = 'unlikes_received_count'

@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ['referrer', 'referred_user', 'status', 'points_awarded', 'created_at', 'completed_at']
    list_filter = ['status', 'created_at']
    search_fields = ['referrer__username', 'referred_user__username']
    readonly_fields = ['created_at', 'completed_at']

admin.site.register(CustomUser, CustomUserAdmin)
