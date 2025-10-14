# payments/admin.py
from django.contrib import admin
from django.db.models import Q
from .models import Package, Purchase

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

@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'price_display', 'currency', 'likes_count', 'boosters', 'is_active', 'has_boosters']
    list_filter = ['is_active', 'currency', HasBoostersFilter]
    search_fields = ['name', 'description']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'currency', 'price', 'is_active')
        }),
        ('Package Contents', {
            'fields': ('likes_count', 'boosters'),
            'description': 'Configure what this package includes. Likes can be used for either likes or dislikes.'
        }),
    )

    def price_display(self, obj):
        currency_symbol = '€' if obj.currency == 'EUR' else 'GH₵'
        return f"{currency_symbol}{obj.price}"
    price_display.short_description = 'Price'
    price_display.admin_order_field = 'price'

    def has_boosters(self, obj):
        return obj.boosters > 0
    has_boosters.boolean = True
    has_boosters.short_description = 'Has Boosters'

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ['user', 'package_name', 'usage_type', 'amount', 'status', 'created_at']
    list_filter = ['status', 'usage_type', 'created_at']
    search_fields = ['user__username', 'package__name']

    def package_name(self, obj):
        return obj.package.name if obj.package else "Unknown Package"
    package_name.short_description = 'Package Name'