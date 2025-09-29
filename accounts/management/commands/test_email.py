from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
import traceback

class Command(BaseCommand):
    help = 'Test email configuration'

    def handle(self, *args, **options):
        try:
            self.stdout.write('Testing email configuration...')
            self.stdout.write(f'Email backend: {settings.EMAIL_BACKEND}')
            
            if 'smtp' in settings.EMAIL_BACKEND:
                self.stdout.write(f'SMTP Host: {getattr(settings, "EMAIL_HOST", "Not set")}')
                self.stdout.write(f'SMTP Port: {getattr(settings, "EMAIL_PORT", "Not set")}')
                self.stdout.write(f'TLS: {getattr(settings, "EMAIL_USE_TLS", "Not set")}')
                self.stdout.write(f'SSL: {getattr(settings, "EMAIL_USE_SSL", "Not set")}')
                self.stdout.write(f'User: {getattr(settings, "EMAIL_HOST_USER", "Not set")}')
                
            # Send test email
            send_mail(
                subject='Test Email from Mooibanana',
                message='This is a test email to verify the email configuration.',
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', settings.EMAIL_HOST_USER),
                recipient_list=['kennedyakogokweku@gmail.com'],
                fail_silently=False,
            )
            self.stdout.write(
                self.style.SUCCESS('Email sent successfully!')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Email failed: {str(e)}')
            )
            self.stdout.write(
                self.style.ERROR(f'Traceback: {traceback.format_exc()}')
            )