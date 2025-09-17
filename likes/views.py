
# likes/views.py
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.db.models import Q
from .models import Like
from chat.models import Match, ChatRoom

User = get_user_model()

@login_required
def give_like(request, user_id):
    if request.method == 'POST':
        target_user = get_object_or_404(User, id=user_id)
        like_type = request.POST.get('like_type', 'regular')
        
        # Check if user has enough likes based on like type
        if like_type == 'super':
            if request.user.super_likes_balance <= 0:
                messages.error(request, 'You need more super likes! Buy a like package.')
                return redirect('payments:packages')
        else:
            if request.user.likes_balance <= 0:
                messages.error(request, 'You need more likes! Buy a like package.')
                return redirect('payments:packages')
        
        # Allow multiple likes to the same person - no duplicate check needed
        
        # Create the like
        like = Like.objects.create(
            from_user=request.user,
            to_user=target_user,
            like_type=like_type
        )
        
        # Deduct like from balance based on type
        if like_type == 'super':
            request.user.super_likes_balance -= 1
        else:
            request.user.likes_balance -= 1
        request.user.save()
        
        # Check for mutual like and create match
        if like.is_mutual:
            match, created = Match.objects.get_or_create(
                user1=min(request.user, target_user, key=lambda u: u.id),
                user2=max(request.user, target_user, key=lambda u: u.id)
            )
            messages.success(request, f'It\'s a match! You can now chat with {target_user.username}.')
            return redirect('chat:room', room_id=match.chat_room.id)
        else:
            messages.success(request, f'You liked {target_user.username}!')
        
        return redirect('profiles:discover')
    
    return redirect('profiles:discover')

class MyLikesView(LoginRequiredMixin, ListView):
    template_name = 'likes/my_likes.html'
    context_object_name = 'likes'
    
    def get_queryset(self):
        return Like.objects.filter(from_user=self.request.user).select_related('to_user__profile')

class MatchesView(LoginRequiredMixin, ListView):
    template_name = 'likes/matches.html'
    context_object_name = 'matches'
    
    def get_queryset(self):
        return Match.objects.filter(
            Q(user1=self.request.user) | Q(user2=self.request.user)
        ).select_related('user1__profile', 'user2__profile')