
# accounts/views.py
from django.shortcuts import render, redirect
from django.views.generic import CreateView, TemplateView, ListView
from django.contrib.auth import login
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.views import PasswordResetView
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
import logging
from .forms import CustomUserCreationForm, CustomPasswordResetForm, UserSettingsForm
from .models import CustomUser, Referral
from django.views.generic.edit import UpdateView

logger = logging.getLogger(__name__)

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


class CustomPasswordResetView(PasswordResetView):
    """Custom password reset view with better error handling and email validation"""
    template_name = 'registration/password_reset_form.html'
    email_template_name = 'registration/password_reset_email.txt'  # Plain text template
    html_email_template_name = 'registration/password_reset_email.html'  # HTML template
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('accounts:password_reset_done')
    form_class = CustomPasswordResetForm
    
    def form_valid(self, form):
        """Override to add better error handling and console fallback"""
        try:
            # Try to send email normally
            return super().form_valid(form)
        except Exception as e:
            logger.error(f"Failed to send password reset email: {str(e)}")
            
            # If SMTP fails, try to provide helpful message
            if 'console' not in settings.EMAIL_BACKEND:
                messages.warning(
                    self.request,
                    'There was an issue sending the email. Please check your email '
                    'configuration or contact the administrator. '
                    'For testing, the system is using console output for emails.'
                )
                
                # Fall back to console output for testing
                email = form.cleaned_data['email']
                reset_url = self.request.build_absolute_uri(
                    reverse_lazy('accounts:password_reset_confirm', 
                               kwargs={'uidb64': 'test', 'token': 'test'})
                )
                
                print(f"\n{'='*50}")
                print("PASSWORD RESET EMAIL (Console Output)")
                print(f"{'='*50}")
                print(f"To: {email}")
                print(f"Subject: Password reset for your Mooibanana account")
                print(f"\nHello,")
                print(f"You requested a password reset for your Mooibanana account.")
                print(f"Reset URL: {reset_url}")
                print(f"{'='*50}\n")
            
            return redirect(self.success_url)


class UserSettingsView(LoginRequiredMixin, UpdateView):
    """View for users to update their account settings including country"""
    model = CustomUser
    form_class = UserSettingsForm
    template_name = 'accounts/settings.html'
    success_url = reverse_lazy('accounts:settings')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Your settings have been updated successfully!')
        return super().form_valid(form)