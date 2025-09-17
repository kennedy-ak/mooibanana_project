# rewards/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Reward(models.Model):
    REWARD_TYPES = [
        ('physical', 'Physical Item'),
        ('digital', 'Digital Item'),
        ('discount', 'Discount Voucher'),
        ('experience', 'Experience'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    points_cost = models.IntegerField()
    reward_type = models.CharField(max_length=20, choices=REWARD_TYPES)
    image = models.ImageField(upload_to='rewards/', blank=True)
    stock_quantity = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class RewardClaim(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rewards_claims')
    reward = models.ForeignKey(Reward, on_delete=models.CASCADE, related_name='rewards_claims')
    points_spent = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    claimed_at = models.DateTimeField(auto_now_add=True)
    delivery_address = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.user.username} claimed {self.reward.name}"

class Like(models.Model):
    LIKE_TYPES = [
        ('regular', 'Regular Like'),
        ('super', 'Super Like'),
    ]
    
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rewards_likes_given')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rewards_likes_received')
    like_type = models.CharField(max_length=10, choices=LIKE_TYPES, default='regular')
    created_at = models.DateTimeField(auto_now_add=True)
    is_mutual = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['from_user', 'to_user']
    
    def __str__(self):
        return f"{self.from_user.username} liked {self.to_user.username} (rewards)"