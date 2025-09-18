
# likes/views.py
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.db.models import Q
from .models import Like, Unlike
from chat.models import Match, ChatRoom
from notifications.models import Notification

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
        
        # Create notification for the user who received the like
        like_type_display = "Super Like" if like_type == 'super' else "Like"
        Notification.objects.create(
            sender=request.user,
            receiver=target_user,
            notification_type='like_received',
            message=f"{request.user.username} gave you a {like_type_display}!",
            status='read'
        )
        
        # Deduct like from balance based on type
        if like_type == 'super':
            request.user.super_likes_balance -= 1
        else:
            request.user.likes_balance -= 1
        request.user.save()
        
        # TEMPORARILY DISABLED - Check for mutual like and create match
        # if like.is_mutual:
        #     match, created = Match.objects.get_or_create(
        #         user1=min(request.user, target_user, key=lambda u: u.id),
        #         user2=max(request.user, target_user, key=lambda u: u.id)
        #     )
        #     messages.success(request, f'It\'s a match! You can now chat with {target_user.username}.')
        #     return redirect('chat:room', room_id=match.chat_room.id)
        # else:
        #     messages.success(request, f'You liked {target_user.username}!')

        # For now, just show like success message
        if like.is_mutual:
            messages.success(request, f'It\'s a mutual like with {target_user.username}! (Chat feature temporarily disabled)')
        else:
            messages.success(request, f'You liked {target_user.username}!')

        return redirect('profiles:discover')
    
    return redirect('profiles:discover')

class MyLikesView(LoginRequiredMixin, ListView):
    template_name = 'likes/my_likes.html'
    context_object_name = 'likes'
    
    def get_queryset(self):
        return Like.objects.filter(from_user=self.request.user).select_related('to_user__profile')

# MATCHES REMOVED FROM SYSTEM
# class MatchesView(LoginRequiredMixin, ListView):
#     template_name = 'likes/matches.html'
#     context_object_name = 'matches'
#
#     def get_queryset(self):
#         return Match.objects.filter(
#             Q(user1=self.request.user) | Q(user2=self.request.user)
#         ).select_related('user1__profile', 'user2__profile')

@login_required
def give_unlike(request, user_id):
    if request.method == 'POST':
        target_user = get_object_or_404(User, id=user_id)

        # Check if user has enough unlikes
        if request.user.unlikes_balance <= 0:
            messages.error(request, 'You need more unlikes! Buy an unlike package.')
            return redirect('payments:packages')

        # Check if user has already unliked this person
        existing_unlike = Unlike.objects.filter(
            from_user=request.user,
            to_user=target_user
        ).first()

        if existing_unlike:
            messages.warning(request, f'You have already unliked {target_user.username}.')
            return redirect('profiles:discover')

        # Create the unlike
        Unlike.objects.create(
            from_user=request.user,
            to_user=target_user
        )

        # Create notification for the user who received the unlike
        Notification.objects.create(
            sender=request.user,
            receiver=target_user,
            notification_type='unlike_received',
            message=f"{request.user.username} sent you a dislike.",
            status='read'
        )

        # Deduct unlike from balance
        request.user.unlikes_balance -= 1
        request.user.save()

        # Remove any existing likes between these users
        Like.objects.filter(
            from_user=request.user,
            to_user=target_user
        ).delete()

        messages.success(request, f'You unliked {target_user.username}. They will no longer appear in your discover feed.')
        return redirect('profiles:discover')

    return redirect('profiles:discover')