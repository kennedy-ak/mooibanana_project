from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
import os

User = get_user_model()

class Command(BaseCommand):
    help = 'Preview the styled password reset email'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address to use for preview (defaults to first user)',
        )
        parser.add_argument(
            '--save',
            action='store_true',
            help='Save the HTML email to a file for viewing in browser',
        )

    def handle(self, *args, **options):
        # Get user for preview
        email = options.get('email')
        if email:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User with email {email} not found'))
                return
        else:
            user = User.objects.first()
            if not user:
                self.stdout.write(self.style.ERROR('No users found in database'))
                return

        # Generate token and uid for preview
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Context for email template
        context = {
            'user': user,
            'protocol': 'https',
            'domain': 'yourdomain.com',
            'uid': uid,
            'token': token,
        }

        # Render HTML email
        html_content = render_to_string('registration/password_reset_email.html', context)
        
        # Render text email
        text_content = render_to_string('registration/password_reset_email.txt', context)

        self.stdout.write(self.style.SUCCESS(f'Email preview for: {user.email}'))
        self.stdout.write('=' * 60)
        
        if options.get('save'):
            # Save HTML to file
            filename = 'password_reset_email_preview.html'
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            self.stdout.write(self.style.SUCCESS(f'HTML email saved to: {filename}'))
            self.stdout.write('Open this file in your browser to see the styled email.')
        
        self.stdout.write('\nPlain text version:')
        self.stdout.write('-' * 30)
        self.stdout.write(text_content)
        
        self.stdout.write('\nHTML version (first 500 chars):')
        self.stdout.write('-' * 30)
        self.stdout.write(html_content[:500] + '...')