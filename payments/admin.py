# payments/admin.py
from django.contrib import admin
from django.db.models import Q
from .models import LikePackage, DislikePackage, Purchase

class HasUnlikesFilter(admin.SimpleListFilter):
    title = 'has unlikes'
    parameter_name = 'has_unlikes'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Yes'),
            ('no', 'No'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(unlikes__gt=0)
        if self.value() == 'no':
            return queryset.filter(unlikes=0)

class HasBoostersFilter(admin.SimpleListFilter):
    title = 'has boosters'
    parameter_name = 'has_boosters'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Yes'),
            ('no', 'No'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(boosters__gt=0)
        if self.value() == 'no':
            return queryset.filter(boosters=0)

@admin.register(LikePackage)
class LikePackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'regular_likes', 'super_likes', 'boosters', 'is_active', 'has_boosters']
    list_filter = ['is_active', HasBoostersFilter]
    search_fields = ['name', 'description']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'price', 'is_active')
        }),
        ('Package Contents', {
            'fields': ('regular_likes', 'super_likes', 'boosters'),
            'description': 'Configure what this like package includes'
        }),
    )
    
    def has_boosters(self, obj):
        return obj.boosters > 0
    has_boosters.boolean = True
    has_boosters.short_description = 'Has Boosters'

@admin.register(DislikePackage)
class DislikePackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'unlikes', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'price', 'is_active')
        }),
        ('Package Contents', {
            'fields': ('unlikes',),
            'description': 'Configure what this dislike package includes'
        }),
    )

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ['user', 'package_type', 'package_name', 'amount', 'status', 'created_at']
    list_filter = ['status', 'package_type', 'created_at']
    search_fields = ['user__username', 'like_package__name', 'dislike_package__name']
    
    def package_name(self, obj):
        return obj.package.name if obj.package else "Unknown Package"
    package_name.short_description = 'Package Name'