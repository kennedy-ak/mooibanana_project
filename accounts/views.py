
# accounts/views.py
from django.shortcuts import render, redirect
from django.views.generic import CreateView, TemplateView, ListView
from django.contrib.auth import login
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.views import PasswordResetView, LoginView
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
import logging
from .forms import CustomUserCreationForm, CustomPasswordResetForm, UserSettingsForm
from .models import CustomUser, Referral
from django.views.generic.edit import UpdateView

logger = logging.getLogger('accounts')


class CustomLoginView(LoginView):
    """Custom login view that always redirects to discover page"""
    template_name = 'accounts/login.html'

    def get_success_url(self):
        """Always redirect to discover page, ignoring 'next' parameter"""
        return reverse_lazy('profiles:discover')

    def form_valid(self, form):
        """Log successful login"""
        response = super().form_valid(form)
        logger.info(f"User logged in successfully - UserID: {self.request.user.id}, Username: {self.request.user.username}")
        return response

    def form_invalid(self, form):
        """Log failed login attempts"""
        username = form.data.get('username', 'unknown')
        logger.warning(f"Failed login attempt - Username: {username}")
        return super().form_invalid(form)

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

        # Log user registration
        logger.info(f"New user registered - UserID: {self.object.id}, Username: {self.object.username}, Email: {self.object.email}")

        # Check if user was referred
        if self.object.referred_by:
            logger.info(f"User registered with referral - UserID: {self.object.id}, ReferredBy: {self.object.referred_by.id}, ReferralCode: {form.cleaned_data.get('referral_code')}")
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

        logger.info(f"Referral link generated - UserID: {request.user.id}, ReferralCode: {referral_code}")

        return JsonResponse({
            'success': True,
            'referral_link': referral_link,
            'referral_code': referral_code
        })

    logger.warning(f"Invalid referral link generation attempt - UserID: {request.user.id}, Method: {request.method}")
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
        email = form.cleaned_data.get('email', 'unknown')
        logger.info(f"Password reset requested - Email: {email}")

        try:
            # Try to send email normally
            response = super().form_valid(form)
            logger.info(f"Password reset email sent successfully - Email: {email}")
            return response
        except Exception as e:
            logger.exception(f"Failed to send password reset email - Email: {email}, Error: {str(e)}")

            # If SMTP fails, try to provide helpful message
            if 'console' not in settings.EMAIL_BACKEND:
                messages.warning(
                    self.request,
                    'There was an issue sending the email. Please check your email '
                    'configuration or contact the administrator. '
                    'For testing, the system is using console output for emails.'
                )

                # Fall back to console output for testing
                reset_url = self.request.build_absolute_uri(
                    reverse_lazy('accounts:password_reset_confirm',
                               kwargs={'uidb64': 'test', 'token': 'test'})
                )

                logger.debug(f"Password reset fallback - Email: {email}, ResetURL: {reset_url}")

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
        # Log what changed
        changed_data = form.changed_data
        if changed_data:
            logger.info(f"User settings updated - UserID: {self.request.user.id}, ChangedFields: {', '.join(changed_data)}")
            if 'country' in changed_data:
                logger.info(f"User country changed - UserID: {self.request.user.id}, NewCountry: {form.cleaned_data.get('country')}")

        messages.success(self.request, 'Your settings have been updated successfully!')
        return super().form_valid(form)