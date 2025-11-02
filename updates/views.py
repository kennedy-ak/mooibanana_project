from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from django.core.cache import cache
from .models import TextUpdate
from social.models import Follow
import json

class UpdatesFeedView(LoginRequiredMixin, View):
    """API endpoint to fetch updates for the sliding feed"""

    def get(self, request):
        # Cache updates feed for 60 seconds to reduce database load
        cache_key = f'updates_feed_{request.user.id}'
        cached_data = cache.get(cache_key)

        if cached_data is not None:
            return JsonResponse(cached_data)

        # Get latest 20 active updates from the last 24 hours only
        twenty_four_hours_ago = timezone.now() - timedelta(hours=24)

        # Get users that current user follows
        following_ids = Follow.objects.filter(
            follower=request.user
        ).values_list('following_id', flat=True)

        # Only show updates from followed users and the current user
        # Optimize with select_related
        updates = TextUpdate.objects.filter(
            Q(user_id__in=following_ids) | Q(user=request.user),
            is_active=True,
            created_at__gte=twenty_four_hours_ago
        ).select_related('user', 'user__profile')[:20]
        
        data = [{
            'id': update.id,
            'user': update.user.username,
            'content': update.content,
            'time_ago': update.time_ago,
            'background_color': update.background_color,
            'text_color': update.text_color,
            'profile_pic': update.user.profile.get_primary_photo() if hasattr(update.user, 'profile') and update.user.profile.get_primary_photo() else None
        } for update in updates]

        response_data = {'updates': data}

        # Cache for 60 seconds
        cache.set(cache_key, response_data, 60)

        return JsonResponse(response_data)

@method_decorator(csrf_exempt, name='dispatch')
class PostUpdateView(LoginRequiredMixin, View):
    """API endpoint to post new text updates"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            content = data.get('content', '').strip()
            background_color = data.get('background_color', '#007bff')
            text_color = data.get('text_color', '#ffffff')
            
            if not content:
                return JsonResponse({'error': 'Content is required'}, status=400)
            
            if len(content) > 280:
                return JsonResponse({'error': 'Content must be 280 characters or less'}, status=400)
            
            # Create new update
            update = TextUpdate.objects.create(
                user=request.user,
                content=content,
                background_color=background_color,
                text_color=text_color
            )
            
            return JsonResponse({
                'success': True,
                'update': {
                    'id': update.id,
                    'user': update.user.username,
                    'content': update.content,
                    'time_ago': update.time_ago,
                    'background_color': update.background_color,
                    'text_color': update.text_color,
                    'profile_pic': update.user.profile.get_primary_photo() if hasattr(update.user, 'profile') and update.user.profile.get_primary_photo() else None
                }
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@login_required
def post_update_form(request):
    """Simple form view for posting updates"""
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        background_color = request.POST.get('background_color', '#007bff')
        text_color = request.POST.get('text_color', '#ffffff')
        
        if not content:
            messages.error(request, 'Please enter some content for your update.')
            return redirect(request.META.get('HTTP_REFERER', '/'))
        
        if len(content) > 280:
            messages.error(request, 'Update must be 280 characters or less.')
            return redirect(request.META.get('HTTP_REFERER', '/'))
        
        TextUpdate.objects.create(
            user=request.user,
            content=content,
            background_color=background_color,
            text_color=text_color
        )
        
        messages.success(request, 'Your update has been posted!')
        return redirect(request.META.get('HTTP_REFERER', '/'))
    
    return redirect('/')

class MyUpdatesView(LoginRequiredMixin, View):
    """View user's own updates"""
    
    def get(self, request):
        updates = TextUpdate.objects.filter(user=request.user, is_active=True)
        paginator = Paginator(updates, 10)
        page = request.GET.get('page')
        updates_page = paginator.get_page(page)
        
        return render(request, 'updates/my_updates.html', {
            'updates': updates_page
        })

@login_required
def delete_update(request, update_id):
    """Delete user's own update"""
    if request.method == 'POST':
        try:
            update = TextUpdate.objects.get(id=update_id, user=request.user)
            update.delete()
            return JsonResponse({'success': True})
        except TextUpdate.DoesNotExist:
            return JsonResponse({'error': 'Update not found'}, status=404)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)