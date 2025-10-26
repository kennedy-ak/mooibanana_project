
# profiles/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import CreateView, UpdateView, ListView, DetailView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q, Exists, OuterRef, Sum, Count
from django.db import models
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from datetime import date, timedelta
from .models import Profile, ProfilePhoto
from .forms import ProfileForm, ProfileSearchForm, ProfilePhotoForm
from django.conf import settings
from likes.models import Like, Unlike
from notifications.models import Notification
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import asyncio
from concurrent.futures import ThreadPoolExecutor
from asgiref.sync import sync_to_async

# Helper function for concurrent distance calculations
def calculate_distance_concurrent(user_profile, profiles, max_distance):
    """
    Calculate distances concurrently using ThreadPoolExecutor
    Returns list of profile IDs within max_distance
    """
    profiles_with_distance = []

    def calc_distance(profile):
        distance = user_profile.calculate_distance_to(profile)
        if distance and distance <= max_distance:
            return profile.id
        return None

    # Use ThreadPoolExecutor for concurrent calculations
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(calc_distance, profiles)
        profiles_with_distance = [pid for pid in results if pid is not None]

    return profiles_with_distance

class CreateProfileView(LoginRequiredMixin, CreateView):
    model = Profile
    form_class = ProfileForm
    template_name = 'profiles/create_profile.html'
    success_url = '/profiles/discover/'
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Profile created successfully!')
        return super().form_valid(form)

class EditProfileView(LoginRequiredMixin, UpdateView):
    model = Profile
    form_class = ProfileForm
    template_name = 'profiles/edit_profile.html'
    success_url = '/profiles/my-profile/'
    
    def get_object(self):
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        return profile

class DiscoverView(LoginRequiredMixin, ListView):
    model = Profile
    template_name = 'profiles/discover.html'
    context_object_name = 'profiles'
    paginate_by = 6

    def get_queryset(self):
        # Get users that have been unliked by current user
        unliked_user_ids = Unlike.objects.filter(
            from_user=self.request.user
        ).values_list('to_user_id', flat=True)

        queryset = Profile.objects.filter(
            is_complete=True
        ).exclude(
            user=self.request.user
        ).exclude(
            user_id__in=unliked_user_ids
        ).select_related('user')

        # Get search parameters
        search_query = self.request.GET.get('search_query', '').strip()
        study_field = self.request.GET.get('study_field', '').strip()
        school_name = self.request.GET.get('school_name', '').strip()
        city = self.request.GET.get('city', '').strip()
        interests = self.request.GET.get('interests', '').strip()
        min_age = self.request.GET.get('min_age', '').strip()
        max_age = self.request.GET.get('max_age', '').strip()
        location = self.request.GET.get('location', '').strip()
        max_distance = self.request.GET.get('max_distance', '').strip()

        # Apply search filters
        if search_query:
            queryset = queryset.filter(
                Q(user__username__icontains=search_query) |
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query)
            )

        if study_field:
            queryset = queryset.filter(study_field=study_field)

        if school_name:
            queryset = queryset.filter(school_name__icontains=school_name)

        if city:
            queryset = queryset.filter(city__icontains=city)

        if interests:
            # Split interests by comma and search for any of them
            interest_list = [interest.strip() for interest in interests.split(',') if interest.strip()]
            if interest_list:
                interest_query = Q()
                for interest in interest_list:
                    interest_query |= Q(interests__icontains=interest)
                queryset = queryset.filter(interest_query)

        if location:
            queryset = queryset.filter(location__icontains=location)

        # Age filtering
        if min_age or max_age:
            today = date.today()

            if min_age:
                try:
                    min_age_int = int(min_age)
                    max_birth_date = today - timedelta(days=min_age_int * 365.25)
                    queryset = queryset.filter(birth_date__lte=max_birth_date)
                except (ValueError, TypeError):
                    pass

            if max_age:
                try:
                    max_age_int = int(max_age)
                    min_birth_date = today - timedelta(days=(max_age_int + 1) * 365.25)
                    queryset = queryset.filter(birth_date__gte=min_birth_date)
                except (ValueError, TypeError):
                    pass

        # Distance-based filtering (using concurrent processing for performance)
        if max_distance and self.request.user.profile.latitude and self.request.user.profile.longitude:
            try:
                max_distance_int = int(max_distance)
                # Get profiles with location data
                profiles_to_check = list(queryset.filter(latitude__isnull=False, longitude__isnull=False))

                # Use concurrent processing for distance calculations
                profiles_with_distance = calculate_distance_concurrent(
                    self.request.user.profile,
                    profiles_to_check,
                    max_distance_int
                )

                queryset = queryset.filter(id__in=profiles_with_distance)
            except (ValueError, TypeError):
                pass

        # If no search parameters, randomize order
        if not any([search_query, study_field, interests, min_age, max_age, location]):
            queryset = queryset.order_by('?')
        else:
            # If searching, order by relevance (username match first, then others)
            if search_query:
                # Use Django ORM annotations instead of raw SQL
                from django.db.models import Case, When, Value, IntegerField
                from django.db.models.functions import Lower
                
                queryset = queryset.annotate(
                    username_match=Case(
                        When(user__username__icontains=search_query, then=Value(1)),
                        default=Value(0),
                        output_field=IntegerField()
                    )
                ).order_by('-username_match', 'user__username')
            else:
                queryset = queryset.order_by('user__username')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Cache user-specific data for 5 minutes
        user_id = self.request.user.id
        cache_key_likes = f'user_likes_{user_id}'
        cache_key_matches = f'user_matches_{user_id}'
        cache_key_requests = f'user_requests_{user_id}'

        # Get cached data or compute it
        likes_count_dict = cache.get(cache_key_likes)
        if likes_count_dict is None:
            from django.db.models import Count
            likes_given = Like.objects.filter(
                from_user=self.request.user
            ).values('to_user').annotate(
                like_count=Count('id')
            )
            likes_count_dict = {item['to_user']: item['like_count'] for item in likes_given}
            cache.set(cache_key_likes, likes_count_dict, 300)  # 5 minutes
        context['likes_count_dict'] = likes_count_dict

        # MATCHES REMOVED FROM SYSTEM
        # Check for mutual matches (cached)
        # matched_users = cache.get(cache_key_matches)
        # if matched_users is None:
        #     matched_users = list(Like.objects.filter(
        #         from_user=self.request.user,
        #         is_mutual=True
        #     ).values_list('to_user', flat=True))
        #     cache.set(cache_key_matches, matched_users, 300)  # 5 minutes
        # context['matched_users'] = matched_users

        # Check for pending match requests (cached)
        # pending_requests = cache.get(cache_key_requests)
        # if pending_requests is None:
        #     from notifications.models import Notification
        #     pending_requests = list(Notification.objects.filter(
        #         sender=self.request.user,
        #         notification_type='match_request',
        #         status='pending'
        #     ).values_list('receiver', flat=True))
        #     cache.set(cache_key_requests, pending_requests, 300)  # 5 minutes
        # context['pending_requests'] = pending_requests

        # Add search form with current values
        search_form = ProfileSearchForm(self.request.GET or None)
        context['search_form'] = search_form

        # Add search parameters to context for display
        context['search_params'] = {
            'search_query': self.request.GET.get('search_query', ''),
            'study_field': self.request.GET.get('study_field', ''),
            'school_name': self.request.GET.get('school_name', ''),
            'city': self.request.GET.get('city', ''),
            'interests': self.request.GET.get('interests', ''),
            'min_age': self.request.GET.get('min_age', ''),
            'max_age': self.request.GET.get('max_age', ''),
            'location': self.request.GET.get('location', ''),
            'max_distance': self.request.GET.get('max_distance', ''),
        }

        # Check if any search is active
        context['is_searching'] = any(context['search_params'].values())

        # Add distance information for each profile if user has location (concurrent processing)
        if self.request.user.profile.latitude and self.request.user.profile.longitude:
            profile_distances = {}
            profiles_list = list(context['profiles'])

            def calc_distance_for_display(profile):
                distance = self.request.user.profile.calculate_distance_to(profile)
                if distance:
                    return (profile.id, round(distance, 1))
                return None

            # Use ThreadPoolExecutor for concurrent distance calculations
            with ThreadPoolExecutor(max_workers=10) as executor:
                results = executor.map(calc_distance_for_display, profiles_list)
                for result in results:
                    if result:
                        profile_distances[result[0]] = result[1]

            context['profile_distances'] = profile_distances

        # Add following status for each profile
        from social.models import Follow
        following_ids = set(Follow.objects.filter(
            follower=self.request.user
        ).values_list('following_id', flat=True))
        context['following_ids'] = following_ids

        # Advertisement flags controlled via settings or environment
        context['show_in_grid_ad'] = getattr(settings, 'SHOW_IN_GRID_AD', False)
        context['show_profile_banner_ad'] = getattr(settings, 'SHOW_PROFILE_BANNER_AD', False)

        # Fetch active advertisements for grid display (cached)
        if context['show_in_grid_ad']:
            from advertisements.models import Advertisement
            context['advertisements'] = Advertisement.get_active_ads(limit=3)

        return context

class ProfileDetailView(LoginRequiredMixin, DetailView):
    model = Profile
    template_name = 'profiles/profile_detail.html'
    context_object_name = 'profile'

    def get_queryset(self):
        return Profile.objects.select_related('user').prefetch_related('photos')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # MATCHES REMOVED FROM SYSTEM
        # Check for mutual matches
        # matched_users = Like.objects.filter(
        #     from_user=self.request.user,
        #     is_mutual=True
        # ).values_list('to_user', flat=True)
        # context['matched_users'] = list(matched_users)

        # Check for pending match requests sent by current user
        # from notifications.models import Notification
        # pending_requests = Notification.objects.filter(
        #     sender=self.request.user,
        #     notification_type='match_request',
        #     status='pending'
        # ).values_list('receiver', flat=True)
        # context['pending_requests'] = list(pending_requests)

        # Check if viewing this profile from a match request notification
        notification_id = self.request.GET.get('notification_id')
        if notification_id:
            try:
                notification = Notification.objects.get(
                    id=notification_id,
                    receiver=self.request.user,
                    sender=self.object.user,
                    notification_type='match_request',
                    status='pending'
                )
                context['match_request_notification'] = notification
            except Notification.DoesNotExist:
                pass

        # Check if there's a pending match request from this profile's user to current user
        incoming_request = Notification.objects.filter(
            sender=self.object.user,
            receiver=self.request.user,
            notification_type='match_request',
            status='pending'
        ).first()
        context['incoming_match_request'] = incoming_request

        # Add statistics for received likes and dislikes from the user model fields
        context['received_likes_count'] = self.object.user.received_likes_count
        context['received_dislikes_count'] = self.object.user.received_unlikes_count

        # Add statistics for given likes and dislikes (what this user has given to others)
        context['given_likes_count'] = self.object.user.likes_given.count()
        context['given_dislikes_count'] = self.object.user.unlikes_given.count()

        # Add bank balances if viewing own profile
        if self.request.user == self.object.user:
            context['likes_bank_balance'] = self.object.user.likes_balance

        # Add social features: following/followers counts
        from social.models import Follow, PostLike, CommentLike
        context['followers_count'] = Follow.objects.filter(following=self.object.user).count()
        context['following_count'] = Follow.objects.filter(follower=self.object.user).count()

        # Check if current user is following this profile
        context['is_following'] = Follow.objects.filter(
            follower=self.request.user,
            following=self.object.user
        ).exists() if self.request.user != self.object.user else False

        # Calculate total likes from posts and comments
        post_likes = PostLike.objects.filter(post__author=self.object.user).aggregate(
            total=models.Sum('amount')
        )['total'] or 0

        comment_likes = CommentLike.objects.filter(comment__author=self.object.user).aggregate(
            total=models.Sum('amount')
        )['total'] or 0

        context['total_post_and_comment_likes'] = post_likes + comment_likes

        # Get recent posts by this user
        from social.models import Post
        context['recent_posts'] = Post.objects.filter(
            author=self.object.user
        ).order_by('-created_at')[:5]

        # Advertisement flag for profile banner
        context['show_profile_banner_ad'] = getattr(settings, 'SHOW_PROFILE_BANNER_AD', False)

        # Fetch active advertisements for profile banner (cached)
        if context['show_profile_banner_ad']:
            from advertisements.models import Advertisement
            active_ads = Advertisement.get_active_ads(limit=1)
            context['banner_ad'] = active_ads[0] if active_ads else None

        return context

class MyProfileView(LoginRequiredMixin, DetailView):
    model = Profile
    template_name = 'profiles/my_profile.html'
    context_object_name = 'profile'
    
    def get_object(self):
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        return profile
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add statistics for received likes and dislikes from the user model fields
        context['received_likes_count'] = self.object.user.received_likes_count
        context['received_dislikes_count'] = self.object.user.received_unlikes_count

        # Add statistics for given likes and dislikes (what user has given to others)
        context['given_likes_count'] = self.object.user.likes_given.count()
        context['given_dislikes_count'] = self.object.user.unlikes_given.count()

        # Add bank balances for my profile
        context['likes_bank_balance'] = self.object.user.likes_balance

        # Add social features: following/followers counts
        from social.models import Follow
        context['followers_count'] = Follow.objects.filter(following=self.object.user).count()
        context['following_count'] = Follow.objects.filter(follower=self.object.user).count()

        return context

class PhotoUploadView(LoginRequiredMixin, FormView):
    form_class = ProfilePhotoForm
    template_name = 'profiles/upload_photos.html'
    success_url = '/profiles/my-profile/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        context['profile'] = profile
        context['existing_photos'] = profile.photos.all()
        return context

    def form_valid(self, form):
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        photos = self.request.FILES.getlist('photos')

        # Limit to 6 photos total
        existing_count = profile.photos.count()
        max_new_photos = 6 - existing_count

        if len(photos) > max_new_photos:
            messages.error(self.request, f'You can only upload {max_new_photos} more photos. Maximum is 6 photos total.')
            return self.form_invalid(form)

        # Save each photo
        for i, photo in enumerate(photos):
            ProfilePhoto.objects.create(
                profile=profile,
                image=photo,
                order=existing_count + i
            )

        messages.success(self.request, f'{len(photos)} photo(s) uploaded successfully!')
        return redirect(self.success_url)

@login_required
@require_POST
def delete_photo(request, photo_id):
    try:
        profile = Profile.objects.get(user=request.user)
        photo = ProfilePhoto.objects.get(id=photo_id, profile=profile)
        photo.delete()
        return JsonResponse({'success': True, 'message': 'Photo deleted successfully'})
    except ProfilePhoto.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Photo not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
@require_POST
def reorder_photos(request):
    try:
        profile = Profile.objects.get(user=request.user)
        photo_ids = request.POST.getlist('photo_ids[]')

        for i, photo_id in enumerate(photo_ids):
            ProfilePhoto.objects.filter(id=photo_id, profile=profile).update(order=i)

        return JsonResponse({'success': True, 'message': 'Photos reordered successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})