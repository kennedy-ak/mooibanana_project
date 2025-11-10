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
        ('money', 'Money Reward'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField()
    points_cost = models.IntegerField(default=0)
    reward_type = models.CharField(max_length=20, choices=REWARD_TYPES)
    image = models.ImageField(upload_to='rewards/', blank=True)
    stock_quantity = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # For like-based rewards (money rewards)
    likes_required = models.IntegerField(default=0, help_text="Number of likes required to claim this reward")

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

class PrizeAnnouncement(models.Model):
    PRIZE_POSITIONS = [
        ('1st', '1st Prize'),
        ('2nd', '2nd Prize'),
        ('3rd', '3rd Prize'),
    ]

    title = models.CharField(max_length=200, help_text="Prize title (e.g., '1st Prize - $5,000 Cash!')")
    description = models.TextField(help_text="Prize description")
    prize_value = models.CharField(max_length=100, help_text="Prize value display (e.g., '$5,000' or 'GHS 9,000')")
    position = models.CharField(max_length=10, choices=PRIZE_POSITIONS, unique=True)
    icon = models.CharField(max_length=50, default='fa-trophy', help_text="FontAwesome icon class (e.g., 'fa-trophy', 'fa-plane')")
    background_color = models.CharField(max_length=20, default='#FFD700', help_text="Hex color code for background")

    # Display control
    is_active = models.BooleanField(default=False, help_text="Show this prize in the banner")
    display_order = models.IntegerField(default=0, help_text="Order in the slider (lower numbers first)")

    # Date range for display
    start_date = models.DateTimeField(null=True, blank=True, help_text="When to start showing this banner")
    end_date = models.DateTimeField(null=True, blank=True, help_text="When to stop showing this banner")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'position']
        verbose_name = "Prize Announcement"
        verbose_name_plural = "Prize Announcements"

    def __str__(self):
        return f"{self.get_position_display()} - {self.prize_value}"