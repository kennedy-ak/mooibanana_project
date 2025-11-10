
# rewards/admin.py
from django.contrib import admin
from .models import Reward, RewardClaim, PrizeAnnouncement

@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    list_display = ['name', 'points_cost', 'reward_type', 'stock_quantity', 'is_active']
    list_filter = ['reward_type', 'is_active']
    search_fields = ['name', 'description']

@admin.register(RewardClaim)
class RewardClaimAdmin(admin.ModelAdmin):
    list_display = ['user', 'reward', 'points_spent', 'status', 'claimed_at']
    list_filter = ['status', 'claimed_at']
    search_fields = ['user__username', 'reward__name']

@admin.register(PrizeAnnouncement)
class PrizeAnnouncementAdmin(admin.ModelAdmin):
    list_display = ['position', 'prize_value', 'is_active', 'display_order', 'start_date', 'end_date']
    list_filter = ['is_active', 'position']
    search_fields = ['title', 'description', 'prize_value']
    ordering = ['display_order', 'position']
    fieldsets = (
        ('Prize Information', {
            'fields': ('position', 'title', 'description', 'prize_value')
        }),
        ('Display Settings', {
            'fields': ('icon', 'background_color', 'display_order')
        }),
        ('Activation', {
            'fields': ('is_active', 'start_date', 'end_date')
        }),
    )
