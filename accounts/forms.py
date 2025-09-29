# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from django.contrib.auth import get_user_model
from .models import CustomUser

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    referral_code = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter referral code (optional)',
            'class': 'form-control'
        }),
        help_text='If you have a referral code, enter it here to give your friend points!'
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2', 'referral_code')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['email'].help_text = 'Please use your student email address'

    def clean_referral_code(self):
        referral_code = self.cleaned_data.get('referral_code')
        if referral_code:
            try:
                referrer = CustomUser.objects.get(referral_code=referral_code.upper())
                return referral_code.upper()
            except CustomUser.DoesNotExist:
                raise forms.ValidationError('Invalid referral code.')
        return referral_code

    def save(self, commit=True):
        user = super().save(commit=False)
        referral_code = self.cleaned_data.get('referral_code')

        if referral_code:
            try:
                referrer = CustomUser.objects.get(referral_code=referral_code.upper())
                user.referred_by = referrer
            except CustomUser.DoesNotExist:
                pass  # Should not happen due to clean_referral_code validation

        if commit:
            user.save()
        return user


class CustomPasswordResetForm(PasswordResetForm):
    """Custom password reset form that validates if email exists"""
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Check if any user exists with this email
            if not User.objects.filter(email__iexact=email, is_active=True).exists():
                raise forms.ValidationError(
                    "No account found with this email address. "
                    "Please check your email or create a new account."
                )
        return email
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })