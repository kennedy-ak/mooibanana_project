
# rewards/admin.py
from django.contrib import admin
from .models import Reward, RewardClaim

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
