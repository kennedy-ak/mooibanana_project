# performance_optimizations.py
"""
Performance optimization utilities for Mooibanana dating app
"""

import asyncio
import concurrent.futures
from django.core.cache import cache
from django.db import transaction
from django.db.models import Prefetch
from functools import wraps
import time


def cache_result(timeout=300):
    """
    Decorator to cache function results
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}_{hash(str(args) + str(kwargs))}"
            result = cache.get(cache_key)
            
            if result is None:
                result = func(*args, **kwargs)
                cache.set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator


def async_view(view_func):
    """
    Decorator to make Django views async-compatible
    """
    @wraps(view_func)
    async def async_wrapper(request, *args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, view_func, request, *args, **kwargs)
    return async_wrapper


def run_async_tasks(*tasks):
    """
    Run multiple async tasks concurrently
    Usage: results = run_async_tasks(task1(), task2(), task3())
    """
    async def gather_tasks():
        return await asyncio.gather(*tasks)

    loop = asyncio.get_event_loop()
    return loop.run_until_complete(gather_tasks())


class AsyncHelper:
    """
    Helper class for async operations
    """

    @staticmethod
    async def run_in_parallel(*coroutines):
        """
        Run multiple coroutines in parallel
        """
        return await asyncio.gather(*coroutines)

    @staticmethod
    async def run_with_timeout(coroutine, timeout_seconds=30):
        """
        Run a coroutine with a timeout
        """
        try:
            return await asyncio.wait_for(coroutine, timeout=timeout_seconds)
        except asyncio.TimeoutError:
            print(f"Operation timed out after {timeout_seconds} seconds")
            return None


class DatabaseOptimizer:
    """
    Database optimization utilities
    """
    
    @staticmethod
    def optimize_profile_queries():
        """
        Optimized queryset for profile discovery
        """
        from profiles.models import Profile
        return Profile.objects.select_related('user').prefetch_related(
            Prefetch('photos', to_attr='cached_photos')
        )
    
    @staticmethod
    def optimize_notification_queries(user):
        """
        Optimized queryset for notifications
        """
        from notifications.models import Notification
        return Notification.objects.filter(
            receiver=user
        ).select_related('sender', 'sender__profile').order_by('-created_at')
    
    @staticmethod
    @transaction.atomic
    def bulk_create_notifications(notifications_data):
        """
        Bulk create notifications for better performance
        """
        from notifications.models import Notification
        notifications = [
            Notification(**data) for data in notifications_data
        ]
        return Notification.objects.bulk_create(notifications)


class ConcurrentProcessor:
    """
    Handle concurrent operations for better performance
    """

    @staticmethod
    def process_multiple_profiles(profile_ids, processing_func, max_workers=4):
        """
        Process multiple profiles concurrently
        """
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(processing_func, profile_id): profile_id
                for profile_id in profile_ids
            }

            results = {}
            for future in concurrent.futures.as_completed(futures):
                profile_id = futures[future]
                try:
                    results[profile_id] = future.result()
                except Exception as exc:
                    print(f'Profile {profile_id} generated an exception: {exc}')
                    results[profile_id] = None

            return results

    @staticmethod
    def process_items_concurrent(items, processing_func, max_workers=10):
        """
        Generic concurrent processor for any list of items
        Returns list of results maintaining order
        """
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(processing_func, items))
            return results

    @staticmethod
    def process_bulk_notifications(notification_data_list):
        """
        Create multiple notifications concurrently
        """
        from notifications.models import Notification

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            def create_notification(data):
                return Notification.objects.create(**data)

            results = list(executor.map(create_notification, notification_data_list))
            return results
    
    @staticmethod
    async def async_fetch_user_data(user_id):
        """
        Asynchronously fetch user data
        """
        loop = asyncio.get_event_loop()
        
        # Run database queries in parallel
        tasks = [
            loop.run_in_executor(None, ConcurrentProcessor._get_user_likes, user_id),
            loop.run_in_executor(None, ConcurrentProcessor._get_user_matches, user_id),
            loop.run_in_executor(None, ConcurrentProcessor._get_user_notifications, user_id),
        ]
        
        likes, matches, notifications = await asyncio.gather(*tasks)
        
        return {
            'likes': likes,
            'matches': matches,
            'notifications': notifications
        }
    
    @staticmethod
    def _get_user_likes(user_id):
        from likes.models import Like
        return Like.objects.filter(from_user_id=user_id).count()
    
    @staticmethod
    def _get_user_matches(user_id):
        from likes.models import Like
        return Like.objects.filter(from_user_id=user_id, is_mutual=True).count()
    
    @staticmethod
    def _get_user_notifications(user_id):
        from notifications.models import Notification
        return Notification.objects.filter(receiver_id=user_id, is_read=False).count()


class ImageOptimizer:
    """
    Image processing optimizations
    """
    
    @staticmethod
    def optimize_profile_image(image_path, max_size=(300, 300)):
        """
        Optimize profile images for faster loading
        """
        from PIL import Image
        import os
        
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Resize if too large
                if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Save with optimization
                img.save(image_path, 'JPEG', quality=85, optimize=True)
                
        except Exception as e:
            print(f"Error optimizing image {image_path}: {e}")


class PerformanceMonitor:
    """
    Monitor and log performance metrics
    """
    
    @staticmethod
    def time_function(func):
        """
        Decorator to time function execution
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            
            execution_time = end_time - start_time
            print(f"{func.__name__} executed in {execution_time:.4f} seconds")
            
            # Log slow queries (> 1 second)
            if execution_time > 1.0:
                print(f"SLOW QUERY WARNING: {func.__name__} took {execution_time:.4f}s")
            
            return result
        return wrapper
    
    @staticmethod
    def log_database_queries():
        """
        Log database queries for debugging
        """
        from django.db import connection
        
        print(f"Database queries executed: {len(connection.queries)}")
        for query in connection.queries[-5:]:  # Show last 5 queries
            print(f"Query: {query['sql'][:100]}... Time: {query['time']}s")


# Cache invalidation utilities
class CacheManager:
    """
    Manage cache invalidation
    """
    
    @staticmethod
    def invalidate_user_cache(user_id):
        """
        Invalidate all cache entries for a specific user
        """
        cache_keys = [
            f'user_likes_{user_id}',
            f'user_matches_{user_id}',
            f'user_requests_{user_id}',
            f'user_notifications_{user_id}',
        ]
        
        cache.delete_many(cache_keys)
    
    @staticmethod
    def warm_cache_for_user(user_id):
        """
        Pre-populate cache for a user
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            user = User.objects.get(id=user_id)
            # Trigger cache population by calling the views
            # This would be called during user login or profile updates
            pass
        except User.DoesNotExist:
            pass


# Usage examples and best practices
"""
PERFORMANCE OPTIMIZATION GUIDELINES:

1. DATABASE OPTIMIZATIONS:
   - Use select_related() for ForeignKey relationships
   - Use prefetch_related() for ManyToMany and reverse ForeignKey
   - Add database indexes for frequently queried fields
   - Use bulk operations for multiple database writes
   - Enable connection pooling with CONN_MAX_AGE

2. CACHING STRATEGIES:
   - Cache expensive database queries
   - Cache template fragments for static content
   - Use Redis for production caching (configure in settings)
   - Implement cache invalidation strategies

3. ASYNC/CONCURRENT PROCESSING:
   - Use async views for I/O-bound operations
   - Process multiple items concurrently with ThreadPoolExecutor
   - Avoid blocking operations in the main thread
   - Use sync_to_async for database operations in async views
   - Examples:
     * Distance calculations: Use calculate_distance_concurrent()
     * Bulk notifications: Use ConcurrentProcessor.process_bulk_notifications()
     * Async views: Decorated with @login_required async def view(request)

4. IMAGE OPTIMIZATION:
   - Resize images on upload
   - Use appropriate image formats (WebP, JPEG)
   - Implement lazy loading for images
   - Use CDN for static assets

5. FRONTEND OPTIMIZATIONS:
   - Minimize JavaScript and CSS
   - Use pagination for large datasets
   - Implement infinite scrolling
   - Optimize AJAX requests

6. MONITORING:
   - Log slow database queries
   - Monitor memory usage
   - Track response times
   - Use Django Debug Toolbar in development

7. IMPLEMENTED OPTIMIZATIONS:
   - ✓ Concurrent distance calculations in DiscoverView
   - ✓ Async like/unlike operations
   - ✓ Async notification retrieval
   - ✓ ThreadPoolExecutor for batch processing
   - ✓ Connection pooling (CONN_MAX_AGE)
   - ✓ Select/prefetch related optimizations
"""
