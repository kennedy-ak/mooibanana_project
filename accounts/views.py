
# accounts/views.py
from django.shortcuts import render, redirect
from django.views.generic import CreateView, TemplateView
from django.contrib.auth import login
from django.contrib import messages
from django.urls import reverse_lazy
from .forms import CustomUserCreationForm
from .models import CustomUser

class RegisterView(CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('profiles:create_profile')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, 'Account created successfully! Please complete your profile.')
        return response

class VerifyEmailView(TemplateView):
    template_name = 'accounts/verify_email.html'