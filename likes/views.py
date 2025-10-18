
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
from asgiref.sync import sync_to_async
import asyncio

User = get_user_model()

@login_required
async def give_like(request, user_id):
    """Async version of give_like for better performance"""
    if request.method == 'POST':
        # Async database operations
        @sync_to_async
        def get_target_user(user_id):
            return get_object_or_404(User, id=user_id)

        @sync_to_async
        def create_like_and_notification(from_user, target_user, amount):
            # Create the like with specified amount
            like = Like.objects.create(
                from_user=from_user,
                to_user=target_user,
                amount=amount
            )

            # Create notification for the user who received the like
            amount_text = f"{amount} Like{'s' if amount > 1 else ''}"
            Notification.objects.create(
                sender=from_user,
                receiver=target_user,
                notification_type='like_received',
                message=f"{from_user.username} gave you {amount_text}!",
                status='read'
            )
            return like

        target_user = await get_target_user(user_id)

        # Get the amount from the form (default to 1 if not provided)
        try:
            amount = int(request.POST.get('amount', 1))
            if amount < 1:
                amount = 1
        except (ValueError, TypeError):
            amount = 1

        # Check if user has enough likes
        if request.user.likes_balance < amount:
            messages.error(request, f'You need {amount} likes! You only have {request.user.likes_balance}. Buy more likes.')
            return redirect('payments:packages')

        # Create like and notification concurrently
        like = await create_like_and_notification(request.user, target_user, amount)

        # Balance deduction is handled in the Like model save() method

        # For now, just show like success message
        amount_text = f"{amount} Like{'s' if amount > 1 else ''}"
        if like.is_mutual:
            messages.success(request, f'It\'s a mutual like with {target_user.username}! You gave them {amount_text}. (Chat feature temporarily disabled)')
        else:
            messages.success(request, f'You gave {amount_text} to {target_user.username}!')

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
async def give_unlike(request, user_id):
    """Async version of give_unlike for better performance"""
    if request.method == 'POST':
        # Async database operations
        @sync_to_async
        def get_target_user(user_id):
            return get_object_or_404(User, id=user_id)

        @sync_to_async
        def process_unlike(from_user, target_user, amount):
            # Check if user has already unliked this person
            existing_unlike = Unlike.objects.filter(
                from_user=from_user,
                to_user=target_user
            ).first()

            if existing_unlike:
                # Update the existing unlike amount
                existing_unlike.amount += amount
                existing_unlike.save()
                return 'updated', existing_unlike.amount
            else:
                # Create new unlike
                Unlike.objects.create(
                    from_user=from_user,
                    to_user=target_user,
                    amount=amount
                )
                return 'created', amount

        @sync_to_async
        def create_notification_and_cleanup(from_user, target_user, amount):
            # Create notification for the user who received the unlike
            amount_text = f"{amount} dislike{'s' if amount > 1 else ''}"
            Notification.objects.create(
                sender=from_user,
                receiver=target_user,
                notification_type='unlike_received',
                message=f"{from_user.username} sent you {amount_text}.",
                status='read'
            )

            # Remove any existing likes between these users
            Like.objects.filter(
                from_user=from_user,
                to_user=target_user
            ).delete()

        target_user = await get_target_user(user_id)

        # Get the amount from the form (default to 1 if not provided)
        try:
            amount = int(request.POST.get('amount', 1))
            if amount < 1:
                amount = 1
        except (ValueError, TypeError):
            amount = 1

        # Check if user has enough balance (unlikes now use likes_balance)
        if request.user.likes_balance < amount:
            messages.error(request, f'You need {amount} in your balance! You only have {request.user.likes_balance}. Buy more packages.')
            return redirect('payments:packages')

        # Process unlike and create notification concurrently
        action, total_amount = await process_unlike(request.user, target_user, amount)
        await create_notification_and_cleanup(request.user, target_user, amount)

        # Balance deduction is handled in the Unlike model save() method

        amount_text = f"{amount} unlike{'s' if amount > 1 else ''}"
        if action == 'updated':
            messages.success(request, f'You added {amount_text} to {target_user.username}. Total unlikes: {total_amount}')
        else:
            messages.success(request, f'You gave {amount_text} to {target_user.username}. They will no longer appear in your discover feed.')

        return redirect('profiles:discover')

    return redirect('profiles:discover')