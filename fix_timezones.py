#!/usr/bin/env python
"""
Fix naive datetimes in database by adding timezone info
Run with: python fix_timezones.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mooibanana_project.settings')
django.setup()

from django.utils import timezone
from django.contrib.auth import get_user_model
from chat.models import Match
from likes.models import Like

User = get_user_model()

def fix_naive_datetimes():
    """Add timezone to naive datetime fields"""

    fixed_count = 0

    # Fix CustomUser.date_joined
    print("Fixing CustomUser.date_joined...")
    for user in User.objects.all():
        if user.date_joined and timezone.is_naive(user.date_joined):
            user.date_joined = timezone.make_aware(user.date_joined)
            user.save(update_fields=['date_joined'])
            fixed_count += 1

    # Fix Match.created_at
    print("Fixing Match.created_at...")
    for match in Match.objects.all():
        if match.created_at and timezone.is_naive(match.created_at):
            match.created_at = timezone.make_aware(match.created_at)
            match.save(update_fields=['created_at'])
            fixed_count += 1

    # Fix Like.created_at
    print("Fixing Like.created_at...")
    for like in Like.objects.all():
        if like.created_at and timezone.is_naive(like.created_at):
            like.created_at = timezone.make_aware(like.created_at)
            like.save(update_fields=['created_at'])
            fixed_count += 1

    print(f"\n✅ Fixed {fixed_count} naive datetime fields!")

if __name__ == '__main__':
    fix_naive_datetimes()
