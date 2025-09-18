# likes/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()

class Like(models.Model):
    LIKE_TYPES = [
        ('regular', 'Regular Like'),
        ('super', 'Super Like'),
    ]
    
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes_given')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes_received')
    like_type = models.CharField(max_length=10, choices=LIKE_TYPES, default='regular')
    created_at = models.DateTimeField(auto_now_add=True)
    is_mutual = models.BooleanField(default=False)
    
    class Meta:
        # Remove unique constraint to allow multiple likes to same person
        pass

    def __str__(self):
        return f"{self.from_user.username} liked {self.to_user.username} ({self.like_type})"

    def save(self, *args, **kwargs):
        # Check if this creates a mutual like (if both users have liked each other)
        if Like.objects.filter(from_user=self.to_user, to_user=self.from_user).exists():
            self.is_mutual = True
            # Update all reverse likes as mutual as well
            Like.objects.filter(from_user=self.to_user, to_user=self.from_user).update(is_mutual=True)

        super().save(*args, **kwargs)

@receiver(post_save, sender=Like)
def award_points_for_like(sender, instance, created, **kwargs):
    if created:
        # Award points to both users
        if instance.like_type == 'regular':
            instance.from_user.points_balance += 5
            instance.to_user.points_balance += 10
        else:  # super like
            instance.from_user.points_balance += 10
            instance.to_user.points_balance += 20
        
        # Bonus for mutual likes
        if instance.is_mutual:
            instance.from_user.points_balance += 25
            instance.to_user.points_balance += 25
        
        instance.from_user.save()
        instance.to_user.save()

class Unlike(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='unlikes_given')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='unlikes_received')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['from_user', 'to_user']

    def __str__(self):
        return f"{self.from_user.username} unliked {self.to_user.username}"

class RewardClaim(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes_reward_claims')
    reward = models.ForeignKey('rewards.Reward', on_delete=models.CASCADE, related_name='likes_claims')
    points_spent = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    claimed_at = models.DateTimeField(auto_now_add=True)
    delivery_address = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.user.username} claimed {self.reward.name}"