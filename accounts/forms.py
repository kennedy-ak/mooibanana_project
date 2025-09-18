# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

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