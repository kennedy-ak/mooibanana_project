# payments/management/commands/create_packages.py
from django.core.management.base import BaseCommand
from payments.models import LikePackage

class Command(BaseCommand):
    help = 'Create default like packages'

    def handle(self, *args, **options):
        # Clear existing packages
        LikePackage.objects.all().delete()
        
        # Create the three packages from the screenshot
        packages = [
            {
                'name': 'Starter Package',
                'price': 4.99,
                'regular_likes': 50,
                'super_likes': 5,
                'boosters': 0,
                'description': 'Basic Profile View - Perfect for getting started with Mooibanana',
                'is_active': True
            },
            {
                'name': 'Popular Package',
                'price': 9.99,
                'regular_likes': 120,
                'super_likes': 15,
                'boosters': 2,
                'description': 'Improved profile display - Most popular choice among students',
                'is_active': True
            },
            {
                'name': 'Premium Package',
                'price': 19.99,
                'regular_likes': 300,
                'super_likes': 30,
                'boosters': 5,
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
