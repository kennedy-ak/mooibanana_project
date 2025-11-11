
# rewards/views.py
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView
from django.db.models import Q
import logging
from .models import Reward, RewardClaim, Like

logger = logging.getLogger('rewards')

class RewardsListView(LoginRequiredMixin, ListView):
    model = Reward
    template_name = 'rewards/list.html'
    context_object_name = 'rewards'

    def get_queryset(self):
        # Show active rewards that either have stock OR are money rewards (unlimited)
        return Reward.objects.filter(
            is_active=True
        ).filter(
            Q(stock_quantity__gt=0) | Q(reward_type='money')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Calculate available likes (total received - spent on rewards)
        total_likes = Like.objects.filter(to_user=self.request.user).count()
        available_likes = total_likes - self.request.user.likes_spent_on_rewards
        context['user_likes_count'] = available_likes
        context['total_likes_received'] = total_likes
        context['likes_spent'] = self.request.user.likes_spent_on_rewards
        return context

@login_required
def claim_reward(request, reward_id):
    reward = get_object_or_404(Reward, id=reward_id, is_active=True)
    logger.info(f"Reward claim initiated - User: {request.user.id}, Reward: {reward_id}, RewardType: {reward.reward_type}")

    # Check if this is a like-based reward
    if reward.reward_type == 'money' and reward.likes_required > 0:
        # Calculate available likes (total received - spent on rewards)
        total_likes = Like.objects.filter(to_user=request.user).count()
        available_likes = total_likes - request.user.likes_spent_on_rewards

        logger.debug(f"Like-based reward claim - User: {request.user.id}, TotalLikes: {total_likes}, AvailableLikes: {available_likes}, Required: {reward.likes_required}")

        if available_likes < reward.likes_required:
            logger.warning(f"Insufficient likes for reward - User: {request.user.id}, Required: {reward.likes_required}, Available: {available_likes}")
            messages.error(request, f'You need {reward.likes_required} likes to claim this reward! You currently have {available_likes} available likes.')
            return redirect('rewards:list')

        # Check if user has already claimed this reward
        existing_claim = RewardClaim.objects.filter(user=request.user, reward=reward).first()
        if existing_claim:
            logger.warning(f"Duplicate reward claim attempt - User: {request.user.id}, Reward: {reward_id}")
            messages.error(request, 'You have already claimed this reward!')
            return redirect('rewards:list')

        # Create reward claim for like-based reward
        claim = RewardClaim.objects.create(
            user=request.user,
            reward=reward,
            points_spent=0  # No points spent for like-based rewards
        )

        # Deduct likes from available balance
        old_likes_spent = request.user.likes_spent_on_rewards
        request.user.likes_spent_on_rewards += reward.likes_required
        request.user.save()

        logger.info(f"Like-based reward claimed - User: {request.user.id}, Reward: {reward_id}, ClaimID: {claim.id}, LikesDeducted: {reward.likes_required}, OldLikesSpent: {old_likes_spent}, NewLikesSpent: {request.user.likes_spent_on_rewards}")

        messages.success(request, f'Successfully claimed {reward.name}! {reward.likes_required} likes have been deducted from your balance.')
        return redirect('rewards:my_claims')
    else:
        # Original points-based reward logic
        logger.debug(f"Points-based reward claim - User: {request.user.id}, UserPoints: {request.user.points_balance}, Required: {reward.points_cost}, Stock: {reward.stock_quantity}")

        if request.user.points_balance < reward.points_cost:
            logger.warning(f"Insufficient points for reward - User: {request.user.id}, Required: {reward.points_cost}, Available: {request.user.points_balance}")
            messages.error(request, 'You don\'t have enough points for this reward!')
            return redirect('rewards:list')

        if reward.stock_quantity <= 0:
            logger.warning(f"Reward out of stock - User: {request.user.id}, Reward: {reward_id}")
            messages.error(request, 'This reward is out of stock!')
            return redirect('rewards:list')

        # Create reward claim
        claim = RewardClaim.objects.create(
            user=request.user,
            reward=reward,
            points_spent=reward.points_cost
        )

        # Deduct points and update stock
        old_points = request.user.points_balance
        old_stock = reward.stock_quantity

        request.user.points_balance -= reward.points_cost
        request.user.save()

        reward.stock_quantity -= 1
        reward.save()

        logger.info(f"Points-based reward claimed - User: {request.user.id}, Reward: {reward_id}, ClaimID: {claim.id}, PointsDeducted: {reward.points_cost}, OldPoints: {old_points}, NewPoints: {request.user.points_balance}, OldStock: {old_stock}, NewStock: {reward.stock_quantity}")

        messages.success(request, f'Successfully claimed {reward.name}! Check your claims for delivery status.')
        return redirect('rewards:my_claims')

class MyClaimsView(LoginRequiredMixin, ListView):
    template_name = 'rewards/my_claims.html'
    context_object_name = 'claims'
    
    def get_queryset(self):
        return RewardClaim.objects.filter(user=self.request.user).select_related('reward')
