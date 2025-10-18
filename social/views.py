# social/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Q, Exists, OuterRef, Count
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model

from .models import Follow, Post, Comment, PostLike, CommentLike
from .forms import PostForm, CommentForm, LikeAmountForm

User = get_user_model()


# ============================================================================
# FOLLOW/UNFOLLOW VIEWS
# ============================================================================

@login_required
@require_POST
def follow_user(request, user_id):
    """Follow a user"""
    user_to_follow = get_object_or_404(User, id=user_id)

    if user_to_follow == request.user:
        return JsonResponse({'success': False, 'error': 'Cannot follow yourself'}, status=400)

    follow, created = Follow.objects.get_or_create(
        follower=request.user,
        following=user_to_follow
    )

    if created:
        return JsonResponse({
            'success': True,
            'message': f'You are now following {user_to_follow.username}',
            'following': True
        })
    else:
        return JsonResponse({
            'success': False,
            'error': 'Already following this user'
        }, status=400)


@login_required
@require_POST
def unfollow_user(request, user_id):
    """Unfollow a user"""
    user_to_unfollow = get_object_or_404(User, id=user_id)

    try:
        follow = Follow.objects.get(follower=request.user, following=user_to_unfollow)
        follow.delete()
        return JsonResponse({
            'success': True,
            'message': f'You unfollowed {user_to_unfollow.username}',
            'following': False
        })
    except Follow.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Not following this user'
        }, status=400)


# ============================================================================
# POST VIEWS
# ============================================================================

class FeedView(LoginRequiredMixin, ListView):
    """Home feed showing posts from followed users"""
    model = Post
    template_name = 'social/feed.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        # Get users that current user follows
        following_ids = Follow.objects.filter(
            follower=self.request.user
        ).values_list('following_id', flat=True)

        # Get posts from followed users and the current user
        queryset = Post.objects.filter(
            Q(author_id__in=following_ids) | Q(author=self.request.user)
        ).select_related('author', 'author__profile').prefetch_related(
            'post_likes', 'comments'
        ).order_by('-created_at')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_likes_balance'] = self.request.user.likes_balance
        return context


class PostDetailView(LoginRequiredMixin, DetailView):
    """Detail view for a single post with comments"""
    model = Post
    template_name = 'social/post_detail.html'
    context_object_name = 'post'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_form'] = CommentForm()
        context['like_form'] = LikeAmountForm()

        # Get top-level comments (not replies)
        context['comments'] = self.object.comments.filter(
            parent_comment=None
        ).select_related('author', 'author__profile').prefetch_related('replies')

        context['user_likes_balance'] = self.request.user.likes_balance

        # Check if user is following post author
        context['is_following'] = Follow.objects.filter(
            follower=self.request.user,
            following=self.object.author
        ).exists()

        return context


class CreatePostView(LoginRequiredMixin, CreateView):
    """View for creating a new post"""
    model = Post
    form_class = PostForm
    template_name = 'social/create_post.html'
    success_url = reverse_lazy('social:feed')

    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, 'Post created successfully!')
        return super().form_valid(form)


@login_required
@require_POST
def delete_post(request, post_id):
    """Delete a post (only by author)"""
    post = get_object_or_404(Post, id=post_id)

    if post.author != request.user:
        return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)

    post.delete()
    return JsonResponse({'success': True, 'message': 'Post deleted successfully'})


# ============================================================================
# COMMENT VIEWS
# ============================================================================

@login_required
@require_POST
def add_comment(request, post_id):
    """Add a comment to a post"""
    post = get_object_or_404(Post, id=post_id)

    if not post.allow_comments:
        return JsonResponse({
            'success': False,
            'error': 'Comments are not allowed on this post'
        }, status=403)

    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user

        # Check if this is a reply to another comment
        parent_comment_id = request.POST.get('parent_comment_id')
        if parent_comment_id:
            parent_comment = get_object_or_404(Comment, id=parent_comment_id)
            comment.parent_comment = parent_comment

        comment.save()

        return JsonResponse({
            'success': True,
            'message': 'Comment added successfully',
            'comment_id': comment.id,
            'author': comment.author.username,
            'content': comment.content,
            'created_at': comment.created_at.strftime('%B %d, %Y at %I:%M %p')
        })
    else:
        return JsonResponse({
            'success': False,
            'error': 'Invalid comment data'
        }, status=400)


@login_required
@require_POST
def delete_comment(request, comment_id):
    """Delete a comment (only by author)"""
    comment = get_object_or_404(Comment, id=comment_id)

    if comment.author != request.user:
        return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)

    comment.delete()
    return JsonResponse({'success': True, 'message': 'Comment deleted successfully'})


# ============================================================================
# LIKE VIEWS
# ============================================================================

@login_required
@require_POST
def like_post(request, post_id):
    """Like a post using likes from user's bank"""
    post = get_object_or_404(Post, id=post_id)

    # Get the amount from the request
    amount = int(request.POST.get('amount', 1))

    if amount < 1:
        return JsonResponse({'success': False, 'error': 'Amount must be at least 1'}, status=400)

    # Check if user has enough likes
    if request.user.likes_balance < amount:
        return JsonResponse({
            'success': False,
            'error': f'Insufficient likes. You have {request.user.likes_balance} likes available.'
        }, status=400)

    try:
        # Create the like
        post_like = PostLike.objects.create(
            post=post,
            user=request.user,
            amount=amount
        )

        # Refresh user to get updated balance
        request.user.refresh_from_db()

        return JsonResponse({
            'success': True,
            'message': f'Liked post with {amount} like(s)',
            'new_balance': request.user.likes_balance,
            'post_likes_count': post.likes_count
        })
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def like_comment(request, comment_id):
    """Like a comment using likes from user's bank"""
    comment = get_object_or_404(Comment, id=comment_id)

    # Get the amount from the request
    amount = int(request.POST.get('amount', 1))

    if amount < 1:
        return JsonResponse({'success': False, 'error': 'Amount must be at least 1'}, status=400)

    # Check if user has enough likes
    if request.user.likes_balance < amount:
        return JsonResponse({
            'success': False,
            'error': f'Insufficient likes. You have {request.user.likes_balance} likes available.'
        }, status=400)

    try:
        # Create the like
        comment_like = CommentLike.objects.create(
            comment=comment,
            user=request.user,
            amount=amount
        )

        # Refresh user to get updated balance
        request.user.refresh_from_db()

        return JsonResponse({
            'success': True,
            'message': f'Liked comment with {amount} like(s)',
            'new_balance': request.user.likes_balance,
            'comment_likes_count': comment.likes_count
        })
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ============================================================================
# USER PROFILE VIEWS (Following/Followers)
# ============================================================================

class FollowersListView(LoginRequiredMixin, ListView):
    """View showing a user's followers"""
    template_name = 'social/followers_list.html'
    context_object_name = 'followers'
    paginate_by = 20

    def get_queryset(self):
        self.profile_user = get_object_or_404(User, id=self.kwargs['user_id'])
        return Follow.objects.filter(
            following=self.profile_user
        ).select_related('follower', 'follower__profile')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile_user'] = self.profile_user
        return context


class FollowingListView(LoginRequiredMixin, ListView):
    """View showing who a user is following"""
    template_name = 'social/following_list.html'
    context_object_name = 'following'
    paginate_by = 20

    def get_queryset(self):
        self.profile_user = get_object_or_404(User, id=self.kwargs['user_id'])
        return Follow.objects.filter(
            follower=self.profile_user
        ).select_related('following', 'following__profile')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile_user'] = self.profile_user
        return context
