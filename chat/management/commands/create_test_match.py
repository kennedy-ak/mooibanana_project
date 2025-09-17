# chat/management/commands/create_test_match.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from likes.models import Like
from chat.models import Match, ChatRoom

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a test match between two users for testing chat functionality'

    def add_arguments(self, parser):
        parser.add_argument('user1_email', type=str, help='Email of first user')
        parser.add_argument('user2_email', type=str, help='Email of second user')

    def handle(self, *args, **options):
        try:
            user1 = User.objects.get(email=options['user1_email'])
            user2 = User.objects.get(email=options['user2_email'])
        except User.DoesNotExist as e:
            self.stdout.write(
                self.style.ERROR(f'User not found: {e}')
            )
            return

        # Create mutual likes
        like1, created1 = Like.objects.get_or_create(
            from_user=user1,
            to_user=user2,
            defaults={'like_type': 'regular', 'is_mutual': True}
        )
        
        like2, created2 = Like.objects.get_or_create(
            from_user=user2,
            to_user=user1,
            defaults={'like_type': 'regular', 'is_mutual': True}
        )
        
        # Update both likes to be mutual
        Like.objects.filter(id__in=[like1.id, like2.id]).update(is_mutual=True)
        
        # Create match
        match, created = Match.objects.get_or_create(
            user1=min(user1, user2, key=lambda u: u.id),
            user2=max(user1, user2, key=lambda u: u.id)
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created match between {user1.username} and {user2.username}')
            )
            self.stdout.write(
                self.style.SUCCESS(f'Chat room ID: {match.chat_room.id}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Match already exists between {user1.username} and {user2.username}')
            )
            self.stdout.write(
                self.style.SUCCESS(f'Chat room ID: {match.chat_room.id}')
            )
