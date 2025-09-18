# payments/admin.py
from django.contrib import admin
from django.db.models import Q
from .models import LikePackage, Purchase

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
    list_display = ['name', 'price', 'regular_likes', 'super_likes', 'unlikes', 'boosters', 'is_active', 'has_unlikes', 'has_boosters']
    list_filter = ['is_active', HasUnlikesFilter, HasBoostersFilter]
    search_fields = ['name', 'description']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'price', 'is_active')
        }),
        ('Package Contents', {
            'fields': ('regular_likes', 'super_likes', 'unlikes', 'boosters'),
            'description': 'Configure what this package includes'
        }),
    )
    
    def has_unlikes(self, obj):
        return obj.unlikes > 0
    has_unlikes.boolean = True
    has_unlikes.short_description = 'Has Unlikes'
    
    def has_boosters(self, obj):
        return obj.boosters > 0
    has_boosters.boolean = True
    has_boosters.short_description = 'Has Boosters'

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ['user', 'package', 'amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'package__name']