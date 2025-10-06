# payments/models.py
from django.db import models
from django.contrib.auth import get_user_model
# from django.db.models.signals import post_save
# from django.dispatch import receiver

User = get_user_model()

class LikePackage(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    regular_likes = models.IntegerField()
    super_likes = models.IntegerField(default=0)
    boosters = models.IntegerField(default=0)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - €{self.price}"

class DislikePackage(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    unlikes = models.IntegerField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - €{self.price}"

class Purchase(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    PACKAGE_TYPE_CHOICES = [
        ('like', 'Like Package'),
        ('dislike', 'Dislike Package'),
    ]

    PAYMENT_PROVIDER_CHOICES = [
        ('paystack', 'Paystack'),
        ('stripe', 'Stripe'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_purchases')
    package_type = models.CharField(max_length=10, choices=PACKAGE_TYPE_CHOICES)
    like_package = models.ForeignKey(LikePackage, on_delete=models.CASCADE, related_name='purchases', null=True, blank=True)
    dislike_package = models.ForeignKey(DislikePackage, on_delete=models.CASCADE, related_name='purchases', null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_provider = models.CharField(max_length=20, choices=PAYMENT_PROVIDER_CHOICES, default='paystack')
    paystack_reference = models.CharField(max_length=200, blank=True, null=True)
    stripe_session_id = models.CharField(max_length=200, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    @property
    def package(self):
        """Get the actual package object"""
        if self.package_type == 'like':
            return self.like_package
        elif self.package_type == 'dislike':
            return self.dislike_package
        return None
    
    def __str__(self):
        package_name = self.package.name if self.package else "Unknown Package"
        return f"{self.user.username} - {package_name} - €{self.amount}"

# Disabled - likes are now handled in the payment views to support gift purchases
# @receiver(post_save, sender=Purchase)
# def add_likes_after_purchase(sender, instance, **kwargs):
#     if instance.status == 'completed' and kwargs.get('update_fields') and 'status' in kwargs['update_fields']:
#         # Add likes to user's balance
#         instance.user.likes_balance += instance.package.regular_likes
#         instance.user.save()

class ChatRoom(models.Model):
    participants = models.ManyToManyField(User, related_name='payment_chat_rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        usernames = [user.username for user in self.participants.all()]
        return f"Payment Chat: {', '.join(usernames)}"
    
    @property
    def last_message(self):
        return self.messages.order_by('-timestamp').first()

class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}..."

class Match(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_matches_as_user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_matches_as_user2')
    created_at = models.DateTimeField(auto_now_add=True)
    chat_room = models.OneToOneField(ChatRoom, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        unique_together = ['user1', 'user2']
    
    def __str__(self):
        return f"Payment Match: {self.user1.username} & {self.user2.username}"
    
    def save(self, *args, **kwargs):
        # Create chat room when match is created
        super().save(*args, **kwargs)
        if not self.chat_room:
            chat_room = ChatRoom.objects.create()
            chat_room.participants.add(self.user1, self.user2)
            self.chat_room = chat_room
            self.save()