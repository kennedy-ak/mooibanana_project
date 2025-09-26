from django.shortcuts import render
from django.http import JsonResponse
from .models import Advertisement


def get_active_advertisements(request):
    """API endpoint to fetch active advertisements"""
    ads = Advertisement.objects.filter(is_active=True)
    ads_data = []
    
    for ad in ads:
        ads_data.append({
            'id': ad.id,
            'brand_name': ad.brand_name,
            'flyer_image': ad.flyer_image.url if ad.flyer_image else None,
            'brand_url': ad.brand_url,
            'display_priority': ad.display_priority
        })
    
    return JsonResponse({'advertisements': ads_data})