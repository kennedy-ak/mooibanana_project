# notifications/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('match_request', 'Match Request'),
        ('match_accepted', 'Match Accepted'),
        ('match_declined', 'Match Declined'),
        ('new_message', 'New Message'),
        ('gift_received', 'Gift Received'),
        ('like_received', 'Like Received'),
        ('unlike_received', 'Unlike Received'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('read', 'Read'),
    ]

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['receiver', 'is_read']),
            models.Index(fields=['receiver', 'notification_type', 'status']),
            models.Index(fields=['sender', 'receiver']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.sender.username} -> {self.receiver.username}: {self.get_notification_type_display()}"

    def mark_as_read(self):
        self.is_read = True
        self.save()

    def accept_match_request(self):
        """Accept a match request and create mutual likes"""
        if self.notification_type == 'match_request' and self.status == 'pending':
            from likes.models import Like
            from chat.models import Match

            # Create mutual likes
            like1, created1 = Like.objects.get_or_create(
                from_user=self.sender,
                to_user=self.receiver,
                defaults={'like_type': 'regular', 'is_mutual': True}
            )

            like2, created2 = Like.objects.get_or_create(
                from_user=self.receiver,
                to_user=self.sender,
                defaults={'like_type': 'regular', 'is_mutual': True}
            )

            # Update both likes to be mutual
            Like.objects.filter(
                from_user=self.sender, to_user=self.receiver
            ).update(is_mutual=True)

            Like.objects.filter(
                from_user=self.receiver, to_user=self.sender
            ).update(is_mutual=True)

            # Create match
            match, created = Match.objects.get_or_create(
                user1=min(self.sender, self.receiver, key=lambda u: u.id),
                user2=max(self.sender, self.receiver, key=lambda u: u.id)
            )

            # Update notification status
            self.status = 'accepted'
            self.save()

            # Create acceptance notification for sender
            Notification.objects.create(
                sender=self.receiver,
                receiver=self.sender,
                notification_type='match_accepted',
                message=f"{self.receiver.username} accepted your match request!",
                status='read'
            )

            return match
        return None

    def decline_match_request(self):
        """Decline a match request"""
        if self.notification_type == 'match_request' and self.status == 'pending':
            self.status = 'declined'
            self.save()

            # Create decline notification for sender
            Notification.objects.create(
                sender=self.receiver,
                receiver=self.sender,
                notification_type='match_declined',
                message=f"{self.receiver.username} declined your match request.",
                status='read'
            )
