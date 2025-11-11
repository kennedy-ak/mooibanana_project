# likes/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
import logging

logger = logging.getLogger('likes')

User = get_user_model()

class Like(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes_given')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes_received')
    amount = models.PositiveIntegerField(default=1, help_text="Number of likes given")
    created_at = models.DateTimeField(auto_now_add=True)
    is_mutual = models.BooleanField(default=False)

    class Meta:
        # Remove unique constraint to allow multiple likes to same person
        pass

    def __str__(self):
        return f"{self.from_user.username} gave {self.amount} like(s) to {self.to_user.username}"

    def save(self, *args, **kwargs):
        # Check if user has enough bank balance before saving
        if not self.pk:  # Only check on creation
            logger.info(f"Creating like - From: {self.from_user.id}, To: {self.to_user.id}, Amount: {self.amount}")

            if self.from_user.likes_balance < self.amount:
                logger.warning(f"Insufficient likes balance - User: {self.from_user.id}, Required: {self.amount}, Available: {self.from_user.likes_balance}")
                raise ValueError(f"Insufficient likes balance. Required: {self.amount}, Available: {self.from_user.likes_balance}")

            # Deduct from bank
            old_from_balance = self.from_user.likes_balance
            self.from_user.likes_balance -= self.amount

            # Update receiver's received count
            old_to_received = self.to_user.received_likes_count
            self.to_user.received_likes_count += self.amount

            # Save the users with updated balances
            self.from_user.save()
            self.to_user.save()

            logger.info(f"Like balances updated - Sender: {self.from_user.id}, OldBalance: {old_from_balance}, NewBalance: {self.from_user.likes_balance}, Receiver: {self.to_user.id}, OldReceived: {old_to_received}, NewReceived: {self.to_user.received_likes_count}")

        # Check if this creates a mutual like (if both users have liked each other)
        if Like.objects.filter(from_user=self.to_user, to_user=self.from_user).exists():
            self.is_mutual = True
            # Update all reverse likes as mutual as well
            Like.objects.filter(from_user=self.to_user, to_user=self.from_user).update(is_mutual=True)
            logger.info(f"Mutual like detected - User1: {self.from_user.id}, User2: {self.to_user.id}")

        super().save(*args, **kwargs)

@receiver(post_save, sender=Like)
def award_points_for_like(sender, instance, created, **kwargs):
    if created:
        # Award points based on like amount - 5 points per like for sender, 10 for receiver
        sender_points = 5 * instance.amount
        receiver_points = 10 * instance.amount

        old_sender_points = instance.from_user.points_balance
        old_receiver_points = instance.to_user.points_balance

        instance.from_user.points_balance += sender_points
        instance.to_user.points_balance += receiver_points

        # Bonus for mutual likes (fixed bonus regardless of amount)
        if instance.is_mutual:
            instance.from_user.points_balance += 25
            instance.to_user.points_balance += 25
            logger.info(f"Mutual like bonus awarded - User1: {instance.from_user.id}, User2: {instance.to_user.id}, Bonus: 25 points each")

        instance.from_user.save()
        instance.to_user.save()

        logger.info(f"Like points awarded - Sender: {instance.from_user.id}, Points: {sender_points}, OldPoints: {old_sender_points}, NewPoints: {instance.from_user.points_balance}, Receiver: {instance.to_user.id}, Points: {receiver_points}, OldPoints: {old_receiver_points}, NewPoints: {instance.to_user.points_balance}")

class Unlike(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='unlikes_given')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='unlikes_received')
    amount = models.PositiveIntegerField(default=1, help_text="Number of unlikes given")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['from_user', 'to_user']

    def save(self, *args, **kwargs):
        # Check if user has enough bank balance before saving
        # Unlikes now use the same likes_balance
        if not self.pk:  # Only check on creation
            logger.info(f"Creating unlike - From: {self.from_user.id}, To: {self.to_user.id}, Amount: {self.amount}")

            if self.from_user.likes_balance < self.amount:
                logger.warning(f"Insufficient balance for unlike - User: {self.from_user.id}, Required: {self.amount}, Available: {self.from_user.likes_balance}")
                raise ValueError(f"Insufficient balance. Required: {self.amount}, Available: {self.from_user.likes_balance}")

            # Deduct from likes bank and update receiver's count
            old_from_balance = self.from_user.likes_balance
            old_to_received = self.to_user.received_unlikes_count

            self.from_user.likes_balance -= self.amount
            self.to_user.received_unlikes_count += self.amount

            # Save the users with updated balances
            self.from_user.save()
            self.to_user.save()

            logger.info(f"Unlike balances updated - Sender: {self.from_user.id}, OldBalance: {old_from_balance}, NewBalance: {self.from_user.likes_balance}, Receiver: {self.to_user.id}, OldReceived: {old_to_received}, NewReceived: {self.to_user.received_unlikes_count}")

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.from_user.username} gave {self.amount} unlike(s) to {self.to_user.username}"

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