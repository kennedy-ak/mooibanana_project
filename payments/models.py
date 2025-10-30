# payments/models.py
from django.db import models
from django.contrib.auth import get_user_model
# from django.db.models.signals import post_save
# from django.dispatch import receiver

User = get_user_model()

class Package(models.Model):
    """Unified package that can be used for either likes or dislikes"""
    CURRENCY_CHOICES = [
        ('EUR', 'Euro (€)'),
        ('GHS', 'Ghana Cedis (GH₵)'),
    ]

    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='GHS')
    likes_count = models.IntegerField(help_text="Number of likes included in this package")
    boosters = models.IntegerField(default=0)
    points_reward = models.IntegerField(default=0, help_text="Points awarded when this package is purchased")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        currency_symbol = 'GH₵' if self.currency == 'GHS' else '€'
        return f"{self.name} - {currency_symbol}{self.price}"

# Keep old model names as aliases for backward compatibility during migration
LikePackage = Package

class Purchase(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    USAGE_TYPE_CHOICES = [
        ('likes', 'For Giving Likes'),
        ('dislikes', 'For Giving Dislikes'),
    ]

    PAYMENT_PROVIDER_CHOICES = [
        ('paystack', 'Paystack'),
        ('stripe', 'Stripe'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_purchases')
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='purchases', null=True, blank=True)
    usage_type = models.CharField(max_length=10, choices=USAGE_TYPE_CHOICES, default='likes',
                                   help_text="Whether user will use these for likes or dislikes")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_provider = models.CharField(max_length=20, choices=PAYMENT_PROVIDER_CHOICES, default='paystack')
    paystack_reference = models.CharField(max_length=200, blank=True, null=True)
    stripe_session_id = models.CharField(max_length=200, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        package_name = self.package.name if self.package else "Unknown Package"
        currency_symbol = 'GH₵' if self.package and self.package.currency == 'GHS' else '€'
        return f"{self.user.username} - {package_name} ({self.get_usage_type_display()}) - {currency_symbol}{self.amount}"

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