# payments/admin.py
from django.contrib import admin
from .models import LikePackage, Purchase

@admin.register(LikePackage)
class LikePackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'regular_likes', 'super_likes', 'is_active']
    list_filter = ['is_active']

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ['user', 'package', 'amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'package__name']