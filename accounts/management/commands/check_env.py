from django.core.management.base import BaseCommand
from django.conf import settings
from decouple import config
import os

class Command(BaseCommand):
    help = 'Check environment variable loading'

    def handle(self, *args, **options):
        self.stdout.write('Checking environment variable loading...')
        
        # Check EMAIL_HOST_PASSWORD
        try:
            email_password_config = config('EMAIL_HOST_PASSWORD')
            self.stdout.write(f'✅ config("EMAIL_HOST_PASSWORD"): {email_password_config[:4]}***')
        except Exception as e:
            self.stdout.write(f'❌ config("EMAIL_HOST_PASSWORD") failed: {e}')
        
        try:
            email_password_os = os.getenv('EMAIL_HOST_PASSWORD')
            if email_password_os:
                self.stdout.write(f'✅ os.getenv("EMAIL_HOST_PASSWORD"): {email_password_os[:4]}***')
            else:
                self.stdout.write('❌ os.getenv("EMAIL_HOST_PASSWORD"): None')
        except Exception as e:
            self.stdout.write(f'❌ os.getenv("EMAIL_HOST_PASSWORD") failed: {e}')
        
        # Check Django settings
        try:
            django_password = settings.EMAIL_HOST_PASSWORD
            if django_password:
                self.stdout.write(f'✅ settings.EMAIL_HOST_PASSWORD: {django_password[:4]}***')
            else:
                self.stdout.write('❌ settings.EMAIL_HOST_PASSWORD: None')
        except Exception as e:
            self.stdout.write(f'❌ settings.EMAIL_HOST_PASSWORD failed: {e}')
        
        # Email configuration summary
        self.stdout.write('\n--- Email Configuration Summary ---')
        self.stdout.write(f'EMAIL_BACKEND: {settings.EMAIL_BACKEND}')
        self.stdout.write(f'EMAIL_HOST: {getattr(settings, "EMAIL_HOST", "Not set")}')
        self.stdout.write(f'EMAIL_PORT: {getattr(settings, "EMAIL_PORT", "Not set")}')
        self.stdout.write(f'EMAIL_USE_SSL: {getattr(settings, "EMAIL_USE_SSL", "Not set")}')
        self.stdout.write(f'EMAIL_USE_TLS: {getattr(settings, "EMAIL_USE_TLS", "Not set")}')
        self.stdout.write(f'EMAIL_HOST_USER: {getattr(settings, "EMAIL_HOST_USER", "Not set")}')
        
        if hasattr(settings, 'EMAIL_HOST_PASSWORD') and settings.EMAIL_HOST_PASSWORD:
            self.stdout.write('✅ Email configuration appears complete')
        else:
            self.stdout.write('❌ Email configuration is incomplete')