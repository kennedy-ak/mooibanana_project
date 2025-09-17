# payments/management/commands/test_gift_purchase.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from payments.models import LikePackage, Purchase
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = 'Test gift purchase logic'

    def add_arguments(self, parser):
        parser.add_argument('buyer_email', type=str, help='Email of buyer')
        parser.add_argument('recipient_email', type=str, help='Email of recipient')

    def handle(self, *args, **options):
        try:
            buyer = User.objects.get(email=options['buyer_email'])
            recipient = User.objects.get(email=options['recipient_email'])
            package = LikePackage.objects.first()
            
            if not package:
                self.stdout.write(self.style.ERROR('No packages found'))
                return
                
        except User.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f'User not found: {e}'))
            return

        # Record initial balances
        buyer_initial_likes = buyer.likes_balance
        buyer_initial_super = buyer.super_likes_balance
        recipient_initial_likes = recipient.likes_balance
        recipient_initial_super = recipient.super_likes_balance
        
        self.stdout.write(f'Initial balances:')
        self.stdout.write(f'Buyer ({buyer.username}): {buyer_initial_likes} likes, {buyer_initial_super} super likes')
        self.stdout.write(f'Recipient ({recipient.username}): {recipient_initial_likes} likes, {recipient_initial_super} super likes')
        
        # Simulate gift purchase completion
        purchase = Purchase.objects.create(
            user=buyer,
            package=package,
            amount=package.price,
            status='completed',
            completed_at=timezone.now(),
            paystack_reference=f'test_gift_{buyer.id}_{recipient.id}'
        )
        
        # Simulate the gift logic
        recipient.likes_balance += package.regular_likes
        recipient.save()
        
        buyer.super_likes_balance += package.super_likes
        buyer.save()
        
        # Refresh from database
        buyer.refresh_from_db()
        recipient.refresh_from_db()
        
        self.stdout.write(f'\nAfter gift purchase of {package.name}:')
        self.stdout.write(f'Buyer ({buyer.username}): {buyer.likes_balance} likes (+{buyer.likes_balance - buyer_initial_likes}), {buyer.super_likes_balance} super likes (+{buyer.super_likes_balance - buyer_initial_super})')
        self.stdout.write(f'Recipient ({recipient.username}): {recipient.likes_balance} likes (+{recipient.likes_balance - recipient_initial_likes}), {recipient.super_likes_balance} super likes (+{recipient.super_likes_balance - recipient_initial_super})')
        
        self.stdout.write(self.style.SUCCESS('\nGift purchase test completed!'))
