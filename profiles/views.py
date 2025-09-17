
# profiles/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import CreateView, UpdateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q, Exists, OuterRef
from .models import Profile
from .forms import ProfileForm
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
        # Only exclude own profile - show all other profiles including liked ones
        return Profile.objects.filter(
            is_complete=True
        ).exclude(
            user=self.request.user
        ).order_by('?')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get count of likes given to each user
        from django.db.models import Count
        likes_given = Like.objects.filter(
            from_user=self.request.user
        ).values('to_user').annotate(
            like_count=Count('id')
        )

        # Create a dictionary for easy lookup
        likes_count_dict = {item['to_user']: item['like_count'] for item in likes_given}
        context['likes_count_dict'] = likes_count_dict

        # Check for mutual matches
        matched_users = Like.objects.filter(
            from_user=self.request.user,
            is_mutual=True
        ).values_list('to_user', flat=True)
        context['matched_users'] = list(matched_users)

        return context

class ProfileDetailView(LoginRequiredMixin, DetailView):
    model = Profile
    template_name = 'profiles/profile_detail.html'
    context_object_name = 'profile'

class MyProfileView(LoginRequiredMixin, DetailView):
    model = Profile
    template_name = 'profiles/my_profile.html'
    context_object_name = 'profile'
    
    def get_object(self):
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        return profile