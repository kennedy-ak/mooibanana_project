
# rewards/views.py
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView
from .models import Reward, RewardClaim

class RewardsListView(LoginRequiredMixin, ListView):
    model = Reward
    template_name = 'rewards/list.html'
    context_object_name = 'rewards'
    
    def get_queryset(self):
        return Reward.objects.filter(is_active=True, stock_quantity__gt=0)

@login_required
def claim_reward(request, reward_id):
    reward = get_object_or_404(Reward, id=reward_id, is_active=True)
    
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
