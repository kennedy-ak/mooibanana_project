# notifications/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.views.generic import ListView
from django.contrib.auth import get_user_model
from django.db.models import Q
from .models import Notification
from .utils import broadcast_notification
from asgiref.sync import sync_to_async
import asyncio

User = get_user_model()

@login_required
def send_match_request(request, user_id):
    """Send a match request to another user"""
    if request.method == 'POST':
        target_user = get_object_or_404(User, id=user_id)

        # Check if notification already exists
        existing_notification = Notification.objects.filter(
            sender=request.user,
            receiver=target_user,
            notification_type='match_request',
            status='pending'
        ).first()

        if existing_notification:
            messages.info(request, f'You already sent a match request to {target_user.username}!')
            return redirect('profiles:discover')

        # Create match request notification
        notification = Notification.objects.create(
            sender=request.user,
            receiver=target_user,
            notification_type='match_request',
            message=f"{request.user.username} wants to match with you!"
        )

        # Send real-time notification
        broadcast_notification(notification)

        messages.success(request, f'Match request sent to {target_user.username}!')
        return redirect('profiles:discover')

    return redirect('profiles:discover')

@login_required
def respond_to_match_request(request, notification_id):
    """Accept or decline a match request"""
    if request.method == 'POST':
        notification = get_object_or_404(
            Notification,
            id=notification_id,
            receiver=request.user,
            notification_type='match_request',
            status='pending'
        )

        action = request.POST.get('action')

        if action == 'accept':
            success = notification.accept_match_request()
            if success:
                messages.success(request, f"It's a match with {notification.sender.username}!")
                return JsonResponse({
                    'success': True,
                    'message': f"It's a match with {notification.sender.username}!",
                    'redirect_url': f'/profiles/profile/{notification.sender.id}/'
                })
        elif action == 'decline':
            notification.decline_match_request()
            messages.info(request, f"You declined {notification.sender.username}'s match request.")
            return JsonResponse({
                'success': True,
                'message': f"You declined {notification.sender.username}'s match request."
            })

        return JsonResponse({'success': True})

    return JsonResponse({'success': False})

@login_required
async def get_notifications(request):
    """Get user's notifications as JSON (async for better performance)"""
    # Use sync_to_async for database query
    @sync_to_async
    def get_notifications_data():
        notifications = Notification.objects.filter(
            receiver=request.user,
            is_read=False
        ).select_related('sender')[:10]

        notification_data = []
        for notification in notifications:
            notification_data.append({
                'id': notification.id,
                'sender': notification.sender.username,
                'sender_id': notification.sender.id,
                'type': notification.notification_type,
                'message': notification.message,
                'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M'),
                'status': notification.status,
                'is_read': notification.is_read
            })
        return notification_data

    notification_data = await get_notifications_data()

    return JsonResponse({
        'notifications': notification_data,
        'count': len(notification_data)
    })

@login_required
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    if request.method == 'POST':
        notification = get_object_or_404(
            Notification,
            id=notification_id,
            receiver=request.user
        )
        notification.mark_as_read()
        return JsonResponse({'success': True})

    return JsonResponse({'success': False})

class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'notifications/list.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_queryset(self):
        return Notification.objects.filter(
            receiver=self.request.user
        ).select_related('sender').order_by('-created_at')
