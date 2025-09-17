
# profiles/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import CreateView, UpdateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q, Exists, OuterRef
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from datetime import date, timedelta
from .models import Profile
from .forms import ProfileForm, ProfileSearchForm
from likes.models import Like

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
    paginate_by = 10

    def get_queryset(self):
        queryset = Profile.objects.filter(
            is_complete=True
        ).exclude(
            user=self.request.user
        ).select_related('user')

        # Get search parameters
        search_query = self.request.GET.get('search_query', '').strip()
        study_field = self.request.GET.get('study_field', '').strip()
        interests = self.request.GET.get('interests', '').strip()
        min_age = self.request.GET.get('min_age', '').strip()
        max_age = self.request.GET.get('max_age', '').strip()
        location = self.request.GET.get('location', '').strip()

        # Apply search filters
        if search_query:
            queryset = queryset.filter(
                Q(user__username__icontains=search_query) |
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query)
            )

        if study_field:
            queryset = queryset.filter(study_field=study_field)

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

        # If no search parameters, randomize order
        if not any([search_query, study_field, interests, min_age, max_age, location]):
            queryset = queryset.order_by('?')
        else:
            # If searching, order by relevance (username match first, then others)
            if search_query:
                queryset = queryset.extra(
                    select={
                        'username_match': f"CASE WHEN LOWER(auth_user.username) LIKE LOWER('%{search_query}%') THEN 1 ELSE 0 END"
                    },
                    tables=['auth_user'],
                    where=['profiles_profile.user_id = auth_user.id'],
                    order_by=['-username_match', 'user__username']
                )
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

        # Check for mutual matches (cached)
        matched_users = cache.get(cache_key_matches)
        if matched_users is None:
            matched_users = list(Like.objects.filter(
                from_user=self.request.user,
                is_mutual=True
            ).values_list('to_user', flat=True))
            cache.set(cache_key_matches, matched_users, 300)  # 5 minutes
        context['matched_users'] = matched_users

        # Check for pending match requests (cached)
        pending_requests = cache.get(cache_key_requests)
        if pending_requests is None:
            from notifications.models import Notification
            pending_requests = list(Notification.objects.filter(
                sender=self.request.user,
                notification_type='match_request',
                status='pending'
            ).values_list('receiver', flat=True))
            cache.set(cache_key_requests, pending_requests, 300)  # 5 minutes
        context['pending_requests'] = pending_requests

        # Add search form with current values
        search_form = ProfileSearchForm(self.request.GET or None)
        context['search_form'] = search_form

        # Add search parameters to context for display
        context['search_params'] = {
            'search_query': self.request.GET.get('search_query', ''),
            'study_field': self.request.GET.get('study_field', ''),
            'interests': self.request.GET.get('interests', ''),
            'min_age': self.request.GET.get('min_age', ''),
            'max_age': self.request.GET.get('max_age', ''),
            'location': self.request.GET.get('location', ''),
        }

        # Check if any search is active
        context['is_searching'] = any(context['search_params'].values())

        return context

class ProfileDetailView(LoginRequiredMixin, DetailView):
    model = Profile
    template_name = 'profiles/profile_detail.html'
    context_object_name = 'profile'

    def get_queryset(self):
        return Profile.objects.select_related('user').prefetch_related('photos')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Check for mutual matches
        matched_users = Like.objects.filter(
            from_user=self.request.user,
            is_mutual=True
        ).values_list('to_user', flat=True)
        context['matched_users'] = list(matched_users)

        # Check for pending match requests sent by current user
        from notifications.models import Notification
        pending_requests = Notification.objects.filter(
            sender=self.request.user,
            notification_type='match_request',
            status='pending'
        ).values_list('receiver', flat=True)
        context['pending_requests'] = list(pending_requests)

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

        return context

class MyProfileView(LoginRequiredMixin, DetailView):
    model = Profile
    template_name = 'profiles/my_profile.html'
    context_object_name = 'profile'
    
    def get_object(self):
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        return profile