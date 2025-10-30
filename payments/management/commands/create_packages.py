# payments/management/commands/create_packages.py
from django.core.management.base import BaseCommand
from payments.models import LikePackage

class Command(BaseCommand):
    help = 'Create default like packages'

    def handle(self, *args, **options):
        # Clear existing packages
        LikePackage.objects.all().delete()

        # Create the three packages with updated pricing in Ghana Cedis (GHS)
        packages = [
            {
                'name': 'Starter Package',
                'price': 70.00,
                'currency': 'GHS',
                'likes_count': 50,
                'boosters': 0,
                'points_reward': 10,
                'description': 'Basic Profile View - Perfect for getting started with Mooibanana',
                'is_active': True
            },
            {
                'name': 'Popular Package',
                'price': 150.00,
                'currency': 'GHS',
                'likes_count': 110,
                'boosters': 2,
                'points_reward': 25,
                'description': 'Improved profile display - Most popular choice among students',
                'is_active': True
            },
            {
                'name': 'Premium Package',
                'price': 300.00,
                'currency': 'GHS',
                'likes_count': 250,
                'boosters': 5,
                'points_reward': 50,
                'description': 'Premium Profile View - Exclusive pricing options and maximum visibility',
                'is_active': True
            }
        ]
        
        for package_data in packages:
            package = LikePackage.objects.create(**package_data)
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created package: {package.name}')
            )
        
        self.stdout.write(
            self.style.SUCCESS('All packages created successfully!')
        )
