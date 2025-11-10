
# rewards/views.py
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView
from django.db.models import Q
from .models import Reward, RewardClaim, Like

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

    # Check if this is a like-based reward
    if reward.reward_type == 'money' and reward.likes_required > 0:
        # Calculate available likes (total received - spent on rewards)
        total_likes = Like.objects.filter(to_user=request.user).count()
        available_likes = total_likes - request.user.likes_spent_on_rewards

        if available_likes < reward.likes_required:
            messages.error(request, f'You need {reward.likes_required} likes to claim this reward! You currently have {available_likes} available likes.')
            return redirect('rewards:list')

        # Check if user has already claimed this reward
        existing_claim = RewardClaim.objects.filter(user=request.user, reward=reward).first()
        if existing_claim:
            messages.error(request, 'You have already claimed this reward!')
            return redirect('rewards:list')

        # Create reward claim for like-based reward
        claim = RewardClaim.objects.create(
            user=request.user,
            reward=reward,
            points_spent=0  # No points spent for like-based rewards
        )

        # Deduct likes from available balance
        request.user.likes_spent_on_rewards += reward.likes_required
        request.user.save()

        messages.success(request, f'Successfully claimed {reward.name}! {reward.likes_required} likes have been deducted from your balance.')
        return redirect('rewards:my_claims')
    else:
        # Original points-based reward logic
        if request.user.points_balance < reward.points_cost:
            messages.error(request, 'You don\'t have enough points for this reward!')
            return redirect('rewards:list')

        if reward.stock_quantity <= 0:
            messages.error(request, 'This reward is out of stock!')
            return redirect('rewards:list')

        # Create reward claim
        claim = RewardClaim.objects.create(
            user=request.user,
            reward=reward,
            points_spent=reward.points_cost
        )

        # Deduct points and update stock
        request.user.points_balance -= reward.points_cost
        request.user.save()

        reward.stock_quantity -= 1
        reward.save()

        messages.success(request, f'Successfully claimed {reward.name}! Check your claims for delivery status.')
        return redirect('rewards:my_claims')

class MyClaimsView(LoginRequiredMixin, ListView):
    template_name = 'rewards/my_claims.html'
    context_object_name = 'claims'
    
    def get_queryset(self):
        return RewardClaim.objects.filter(user=self.request.user).select_related('reward')
