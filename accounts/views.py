
# accounts/views.py
from django.shortcuts import render, redirect
from django.views.generic import CreateView, TemplateView, ListView
from django.contrib.auth import login
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .forms import CustomUserCreationForm
from .models import CustomUser, Referral

class RegisterView(CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('profiles:create_profile')

    def get_initial(self):
        initial = super().get_initial()
        # Pre-fill referral code if provided in URL
        ref_code = self.request.GET.get('ref')
        if ref_code:
            initial['referral_code'] = ref_code
        return initial

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)

        # Check if user was referred
        if self.object.referred_by:
            messages.success(
                self.request,
                f'Account created successfully! You were referred by {self.object.referred_by.username}. '
                f'Complete your profile to give them referral points!'
            )
        else:
            messages.success(self.request, 'Account created successfully! Please complete your profile.')

        return response

class VerifyEmailView(TemplateView):
    template_name = 'accounts/verify_email.html'

class ReferralDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/referral_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context.update({
            'referral_code': user.referral_code,
            'referral_count': user.get_referral_count(),
            'referral_points': user.get_referral_points(),
            'total_points': user.points_balance,
            'referrals': Referral.objects.filter(referrer=user).select_related('referred_user'),
            'referred_users': user.referrals.all()
        })
        return context

@login_required
def generate_referral_link(request):
    """Generate a shareable referral link"""
    if request.method == 'GET':
        referral_code = request.user.referral_code
        base_url = request.build_absolute_uri('/accounts/register/')
        referral_link = f"{base_url}?ref={referral_code}"

        return JsonResponse({
            'success': True,
            'referral_link': referral_link,
            'referral_code': referral_code
        })

    return JsonResponse({'success': False, 'message': 'Invalid request method'})