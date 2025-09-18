# notifications/utils.py
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

def send_real_time_notification(user_id, notification_data):
    """
    Send a real-time notification to a specific user via WebSocket
    """
    channel_layer = get_channel_layer()
    
    if channel_layer:
        async_to_sync(channel_layer.group_send)(
            f'notifications_{user_id}',
            {
                'type': 'notification_message',
                'notification': notification_data,
                'count': get_unread_count(user_id)
            }
        )

def get_unread_count(user_id):
    """
    Get the count of unread notifications for a user
    """
    from .models import Notification
    return Notification.objects.filter(
        receiver_id=user_id,
        is_read=False
    ).count()

def broadcast_notification(notification):
    """
    Broadcast a notification in real-time when it's created
    """
    notification_data = {
        'id': notification.id,
        'sender': notification.sender.username,
        'sender_id': notification.sender.id,
        'type': notification.notification_type,
        'message': notification.message,
        'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M'),
        'status': notification.status,
        'is_read': notification.is_read
    }
    
    send_real_time_notification(notification.receiver.id, notification_data)
