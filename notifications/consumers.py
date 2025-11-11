# notifications/consumers.py
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Notification

logger = logging.getLogger('notifications')

User = get_user_model()

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]

        if self.user.is_anonymous:
            logger.warning("Anonymous user attempted WebSocket connection")
            await self.close()
            return

        # Join user-specific notification group
        self.notification_group_name = f'notifications_{self.user.id}'

        await self.channel_layer.group_add(
            self.notification_group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"WebSocket connected - User: {self.user.id}, Channel: {self.channel_name}")

        # Send current unread notifications count
        unread_count = await self.get_unread_count()
        await self.send(text_data=json.dumps({
            'type': 'notification_count',
            'count': unread_count
        }))
        logger.debug(f"Sent unread count to user - User: {self.user.id}, Count: {unread_count}")

    async def disconnect(self, close_code):
        if hasattr(self, 'notification_group_name'):
            await self.channel_layer.group_discard(
                self.notification_group_name,
                self.channel_name
            )
            logger.info(f"WebSocket disconnected - User: {self.user.id}, CloseCode: {close_code}")

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')

            logger.debug(f"WebSocket message received - User: {self.user.id}, Type: {message_type}")

            if message_type == 'mark_read':
                notification_id = text_data_json.get('notification_id')
                result = await self.mark_notification_read(notification_id)
                logger.info(f"Notification marked as read - User: {self.user.id}, NotificationID: {notification_id}, Success: {result}")
            elif message_type == 'get_notifications':
                notifications = await self.get_notifications()
                await self.send(text_data=json.dumps({
                    'type': 'notifications_list',
                    'notifications': notifications
                }))
                logger.debug(f"Sent notifications list - User: {self.user.id}, Count: {len(notifications)}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in WebSocket - User: {self.user.id}, Error: {str(e)}")

    # Receive message from notification group
    async def notification_message(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def get_unread_count(self):
        return Notification.objects.filter(
            receiver=self.user,
            is_read=False
        ).count()

    @database_sync_to_async
    def get_notifications(self):
        notifications = Notification.objects.filter(
            receiver=self.user,
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

    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        try:
            notification = Notification.objects.get(
                id=notification_id,
                receiver=self.user
            )
            notification.mark_as_read()
            return True
        except Notification.DoesNotExist:
            return False
