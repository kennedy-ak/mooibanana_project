# chat/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()
class ChatRoom(models.Model):
    participants = models.ManyToManyField(User, related_name='chat_rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        usernames = [user.username for user in self.participants.all()]
        return f"Chat: {', '.join(usernames)}"
    
    @property
    def last_message(self):
        return self.messages.order_by('-timestamp').first()

class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}..."

class Match(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_matches_as_user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_matches_as_user2')
    created_at = models.DateTimeField(auto_now_add=True)
    chat_room = models.OneToOneField(ChatRoom, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        unique_together = ['user1', 'user2']
    
    def __str__(self):
        return f"Match: {self.user1.username} & {self.user2.username}"
    
    def save(self, *args, **kwargs):
        # Create chat room when match is created
        super().save(*args, **kwargs)
        if not self.chat_room:
            chat_room = ChatRoom.objects.create()
            chat_room.participants.add(self.user1, self.user2)
            self.chat_room = chat_room
            self.save()

class Purchase(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_purchases')
    package = models.ForeignKey('payments.LikePackage', on_delete=models.CASCADE, related_name='chat_purchases')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    stripe_payment_intent_id = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.package.name} - €{self.amount}"