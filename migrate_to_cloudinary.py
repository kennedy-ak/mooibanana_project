#!/usr/bin/env python
"""
Migrate existing local media files to Cloudinary
Run with: python migrate_to_cloudinary.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mooibanana_project.settings')
django.setup()

from django.core.files import File
from django.contrib.auth import get_user_model
from profiles.models import Profile, ProfilePhoto
from advertisements.models import Advertisement
from rewards.models import Reward

User = get_user_model()

def migrate_images():
    """Upload existing local images to Cloudinary"""

    uploaded_count = 0

    print("Migrating Profile pictures...")
    for profile in Profile.objects.exclude(profile_picture=''):
        if profile.profile_picture and hasattr(profile.profile_picture, 'path'):
            try:
                # Check if file exists locally
                if os.path.exists(profile.profile_picture.path):
                    # Re-save the file (this will upload to Cloudinary)
                    with open(profile.profile_picture.path, 'rb') as f:
                        file_name = os.path.basename(profile.profile_picture.name)
                        profile.profile_picture.save(file_name, File(f), save=True)
                    print(f"  Uploaded: {profile.user.username}'s profile picture")
                    uploaded_count += 1
            except Exception as e:
                print(f"  Error with {profile.user.username}: {e}")

    print("\nMigrating Profile photos...")
    for photo in ProfilePhoto.objects.all():
        if photo.image and hasattr(photo.image, 'path'):
            try:
                if os.path.exists(photo.image.path):
                    with open(photo.image.path, 'rb') as f:
                        file_name = os.path.basename(photo.image.name)
                        photo.image.save(file_name, File(f), save=True)
                    print(f"  Uploaded: {photo.profile.user.username}'s photo")
                    uploaded_count += 1
            except Exception as e:
                print(f"  Error: {e}")

    print("\nMigrating Advertisement images...")
    for ad in Advertisement.objects.exclude(flyer_image=''):
        if ad.flyer_image and hasattr(ad.flyer_image, 'path'):
            try:
                if os.path.exists(ad.flyer_image.path):
                    with open(ad.flyer_image.path, 'rb') as f:
                        file_name = os.path.basename(ad.flyer_image.name)
                        ad.flyer_image.save(file_name, File(f), save=True)
                    print(f"  Uploaded: {ad.title}")
                    uploaded_count += 1
            except Exception as e:
                print(f"  Error: {e}")

    print("\nMigrating Reward images...")
    for reward in Reward.objects.exclude(image=''):
        if reward.image and hasattr(reward.image, 'path'):
            try:
                if os.path.exists(reward.image.path):
                    with open(reward.image.path, 'rb') as f:
                        file_name = os.path.basename(reward.image.name)
                        reward.image.save(file_name, File(f), save=True)
                    print(f"  Uploaded: {reward.name}")
                    uploaded_count += 1
            except Exception as e:
                print(f"  Error: {e}")

    print(f"\nMigration complete! Uploaded {uploaded_count} images to Cloudinary")
    print("You can now check your Cloudinary dashboard at https://cloudinary.com/console/media_library")

if __name__ == '__main__':
    migrate_images()
