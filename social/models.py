# social/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum

User = get_user_model()


class Follow(models.Model):
    """Model for user following relationships"""
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['follower', 'following']
        indexes = [
            models.Index(fields=['follower', 'created_at']),
            models.Index(fields=['following', 'created_at']),
        ]

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"

    def clean(self):
        if self.follower == self.following:
            raise ValidationError("Users cannot follow themselves.")


class Post(models.Model):
    """Model for user posts with images and content"""
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField(max_length=5000, help_text="Post content")
    image = models.ImageField(upload_to='posts/', blank=True, null=True)
    allow_comments = models.BooleanField(default=True, help_text="Allow users to comment on this post")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Denormalized counts for performance
    likes_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['author', '-created_at']),
        ]

    def __str__(self):
        return f"Post by {self.author.username} at {self.created_at}"

    def update_likes_count(self):
        """Update the denormalized likes count - sum of all like amounts"""
        total = self.post_likes.aggregate(total=Sum('amount'))['total']
        self.likes_count = total if total is not None else 0
        self.save(update_fields=['likes_count'])

    def update_comments_count(self):
        """Update the denormalized comments count"""
        self.comments_count = self.comments.count()
        self.save(update_fields=['comments_count'])


class Comment(models.Model):
    """Model for comments on posts with nested comment support"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    content = models.TextField(max_length=1000, help_text="Comment content")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Denormalized count for performance
    likes_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['parent_comment', 'created_at']),
            models.Index(fields=['author', '-created_at']),
        ]

    def __str__(self):
        return f"Comment by {self.author.username} on post {self.post.id}"

    def update_likes_count(self):
        """Update the denormalized likes count - sum of all like amounts"""
        total = self.comment_likes.aggregate(total=Sum('amount'))['total']
        self.likes_count = total if total is not None else 0
        self.save(update_fields=['likes_count'])

    def is_reply(self):
        """Check if this comment is a reply to another comment"""
        return self.parent_comment is not None


class PostLike(models.Model):
    """Model for liking posts - uses likes from the user's like bank"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_likes')
    amount = models.PositiveIntegerField(default=1, help_text="Number of likes given")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Allow multiple likes to same post
        indexes = [
            models.Index(fields=['post', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} liked post {self.post.id} with {self.amount} like(s)"

    def save(self, *args, **kwargs):
        # Check if user has enough bank balance before saving
        if not self.pk:  # Only check on creation
            if self.user.likes_balance < self.amount:
                raise ValueError(f"Insufficient likes balance. Required: {self.amount}, Available: {self.user.likes_balance}")

            # Deduct from user's bank
            self.user.likes_balance -= self.amount

            # Add to post author's received likes count
            self.post.author.received_likes_count += self.amount

            # Save the users with updated balances
            self.user.save()
            self.post.author.save()

        super().save(*args, **kwargs)

        # Update post's like count
        self.post.update_likes_count()


class CommentLike(models.Model):
    """Model for liking comments - uses likes from the user's like bank"""
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='comment_likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comment_likes')
    amount = models.PositiveIntegerField(default=1, help_text="Number of likes given")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Allow multiple likes to same comment
        indexes = [
            models.Index(fields=['comment', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} liked comment {self.comment.id} with {self.amount} like(s)"

    def save(self, *args, **kwargs):
        # Check if user has enough bank balance before saving
        if not self.pk:  # Only check on creation
            if self.user.likes_balance < self.amount:
                raise ValueError(f"Insufficient likes balance. Required: {self.amount}, Available: {self.user.likes_balance}")

            # Deduct from user's bank
            self.user.likes_balance -= self.amount

            # Add to comment author's received likes count
            self.comment.author.received_likes_count += self.amount

            # Save the users with updated balances
            self.user.save()
            self.comment.author.save()

        super().save(*args, **kwargs)

        # Update comment's like count
        self.comment.update_likes_count()


# Signals to update comment counts
@receiver(post_save, sender=Comment)
def update_post_comment_count_on_create(sender, instance, created, **kwargs):
    """Update post's comment count when a comment is created"""
    if created:
        instance.post.update_comments_count()


@receiver(post_delete, sender=Comment)
def update_post_comment_count_on_delete(sender, instance, **kwargs):
    """Update post's comment count when a comment is deleted"""
    instance.post.update_comments_count()
