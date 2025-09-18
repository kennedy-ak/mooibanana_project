from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from profiles.models import Profile

User = get_user_model()

class Command(BaseCommand):
    help = 'Create basic profiles for users who don\'t have them'

    def handle(self, *args, **options):
        users_without_profiles = User.objects.filter(profile__isnull=True)
        created_count = 0
        
        for user in users_without_profiles:
            profile = Profile.objects.create(
                user=user,
                bio=f"Hi, I'm {user.first_name or user.username}!",
                is_complete=False  # Set to incomplete since they don't have all required fields
            )
            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(f'Created basic profile for {user.username}')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nCreated {created_count} basic profiles!')
        )