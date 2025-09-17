# profiles/management/commands/optimize_performance.py
from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.db import connection
from profiles.models import Profile
from notifications.models import Notification
from performance_optimizations import ImageOptimizer, CacheManager
import os
from PIL import Image


class Command(BaseCommand):
    help = 'Optimize performance by applying various optimizations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--optimize-images',
            action='store_true',
            help='Optimize all profile images',
        )
        parser.add_argument(
            '--warm-cache',
            action='store_true',
            help='Warm up cache for active users',
        )
        parser.add_argument(
            '--analyze-queries',
            action='store_true',
            help='Analyze database queries',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Run all optimizations',
        )

    def handle(self, *args, **options):
        if options['all']:
            options['optimize_images'] = True
            options['warm_cache'] = True
            options['analyze_queries'] = True

        if options['optimize_images']:
            self.optimize_images()

        if options['warm_cache']:
            self.warm_cache()

        if options['analyze_queries']:
            self.analyze_queries()

        self.stdout.write(
            self.style.SUCCESS('Performance optimization completed!')
        )

    def optimize_images(self):
        """Optimize all profile images"""
        self.stdout.write('Optimizing profile images...')
        
        profiles = Profile.objects.exclude(profile_picture='')
        optimized_count = 0
        
        for profile in profiles:
            if profile.profile_picture and os.path.exists(profile.profile_picture.path):
                try:
                    original_size = os.path.getsize(profile.profile_picture.path)
                    ImageOptimizer.optimize_profile_image(profile.profile_picture.path)
                    new_size = os.path.getsize(profile.profile_picture.path)
                    
                    if new_size < original_size:
                        optimized_count += 1
                        savings = original_size - new_size
                        self.stdout.write(f'Optimized {profile.user.username}: saved {savings} bytes')
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error optimizing {profile.user.username}: {e}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS(f'Optimized {optimized_count} profile images')
        )

    def warm_cache(self):
        """Warm up cache for active users"""
        self.stdout.write('Warming up cache...')
        
        # Get active users (users with complete profiles)
        active_users = Profile.objects.filter(
            is_complete=True
        ).select_related('user')[:100]  # Limit to 100 most recent
        
        warmed_count = 0
        for profile in active_users:
            try:
                CacheManager.warm_cache_for_user(profile.user.id)
                warmed_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error warming cache for {profile.user.username}: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Warmed cache for {warmed_count} users')
        )

    def analyze_queries(self):
        """Analyze database queries for optimization opportunities"""
        self.stdout.write('Analyzing database queries...')
        
        # Reset query log
        connection.queries_log.clear()
        
        # Simulate some common operations
        self.stdout.write('Simulating discover page...')
        profiles = Profile.objects.filter(is_complete=True)[:10]
        for profile in profiles:
            # This will trigger queries - we want to see how many
            _ = profile.user.username
            _ = profile.age
            _ = profile.get_interests_list()
        
        self.stdout.write('Simulating notifications...')
        notifications = Notification.objects.filter(
            receiver_id=1  # Assuming user ID 1 exists
        ).select_related('sender')[:5]
        for notification in notifications:
            _ = notification.sender.username
        
        # Analyze queries
        query_count = len(connection.queries)
        self.stdout.write(f'Total queries executed: {query_count}')
        
        if query_count > 20:
            self.stdout.write(
                self.style.WARNING(
                    f'High query count detected: {query_count}. Consider adding select_related/prefetch_related.'
                )
            )
        
        # Show slow queries
        slow_queries = [q for q in connection.queries if float(q['time']) > 0.1]
        if slow_queries:
            self.stdout.write(
                self.style.WARNING(f'Found {len(slow_queries)} slow queries (>0.1s):')
            )
            for query in slow_queries[:5]:  # Show first 5
                self.stdout.write(f"  Time: {query['time']}s - {query['sql'][:100]}...")
        
        # Cache statistics
        cache_info = cache.get_many(['user_likes_1', 'user_matches_1', 'user_requests_1'])
        cached_items = len([k for k, v in cache_info.items() if v is not None])
        self.stdout.write(f'Cache hits: {cached_items}/3 for user 1')
        
        self.stdout.write(
            self.style.SUCCESS('Query analysis completed')
        )
