# admin_dashboard/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.db.models import Count, Q, Sum, Avg, Max, Min, F, ExpressionWrapper
from django.db.models.functions import TruncDate, ExtractHour, ExtractYear
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DeleteView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from django.utils import timezone

from django.contrib.auth import get_user_model
from profiles.models import Profile
from notifications.models import Notification
from likes.models import Like, Unlike
from quiz.models import Question, Choice, UserQuizResponse, DailyQuiz

# Import models that might not exist
try:
    from chat.models import Match
except ImportError:
    Match = None

try:
    from payments.models import Purchase
except ImportError:
    Purchase = None

User = get_user_model()


def is_superuser(user):
    return user.is_superuser


@user_passes_test(is_superuser)
def admin_dashboard(request):
    """Main admin dashboard with platform statistics"""
    
    # Get date ranges for statistics
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # User statistics
    total_users = User.objects.count()
    total_students = User.objects.filter(is_student=True).count()
    verified_users = User.objects.filter(is_verified=True).count()
    users_this_week = User.objects.filter(date_joined__gte=week_ago).count()
    users_this_month = User.objects.filter(date_joined__gte=month_ago).count()
    
    # Profile statistics
    complete_profiles = Profile.objects.filter(is_complete=True).count()
    incomplete_profiles = Profile.objects.filter(is_complete=False).count()
    profiles_with_photos = Profile.objects.exclude(profile_picture='').count()
    
    # Match statistics
    if Match:
        total_matches = Match.objects.count()
        matches_this_week = Match.objects.filter(created_at__gte=week_ago).count()
        matches_this_month = Match.objects.filter(created_at__gte=month_ago).count()
    else:
        total_matches = matches_this_week = matches_this_month = 0
    
    # Like statistics
    total_likes = Like.objects.count()
    mutual_likes = Like.objects.filter(is_mutual=True).count()
    likes_this_week = Like.objects.filter(created_at__gte=week_ago).count()
    
    # Notification statistics
    total_notifications = Notification.objects.count()
    pending_match_requests = Notification.objects.filter(
        notification_type='match_request',
        status='pending'
    ).count()
    unread_notifications = Notification.objects.filter(is_read=False).count()
    
    # Payment statistics
    if Purchase:
        total_purchases = Purchase.objects.count()
        completed_purchases = Purchase.objects.filter(status='completed').count()
        revenue = Purchase.objects.filter(status='completed').aggregate(
            total=Sum('amount')
        )['total'] or 0
    else:
        total_purchases = completed_purchases = revenue = 0
    
    # Recent activity
    recent_users = User.objects.order_by('-date_joined')[:5]
    recent_matches = Match.objects.select_related('user1', 'user2').order_by('-created_at')[:5] if Match else []
    recent_purchases = Purchase.objects.select_related('user', 'package').order_by('-created_at')[:5] if Purchase else []
    
    # Study field distribution
    study_field_stats = Profile.objects.values('study_field').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    context = {
        'total_users': total_users,
        'total_students': total_students,
        'verified_users': verified_users,
        'users_this_week': users_this_week,
        'users_this_month': users_this_month,
        'complete_profiles': complete_profiles,
        'incomplete_profiles': incomplete_profiles,
        'profiles_with_photos': profiles_with_photos,
        'total_matches': total_matches,
        'matches_this_week': matches_this_week,
        'matches_this_month': matches_this_month,
        'total_likes': total_likes,
        'mutual_likes': mutual_likes,
        'likes_this_week': likes_this_week,
        'total_notifications': total_notifications,
        'pending_match_requests': pending_match_requests,
        'unread_notifications': unread_notifications,
        'total_purchases': total_purchases,
        'completed_purchases': completed_purchases,
        'revenue': revenue,
        'recent_users': recent_users,
        'recent_matches': recent_matches,
        'recent_purchases': recent_purchases,
        'study_field_stats': study_field_stats,
    }
    
    return render(request, 'admin_dashboard/dashboard.html', context)


@method_decorator(user_passes_test(is_superuser), name='dispatch')
class UserManagementView(ListView):
    """User management page with search and filtering"""
    model = User
    template_name = 'admin_dashboard/user_management.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = User.objects.select_related('profile').order_by('-date_joined')
        
        # Search functionality
        search = self.request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        # Filter by user type
        user_type = self.request.GET.get('user_type', '')
        if user_type == 'students':
            queryset = queryset.filter(is_student=True)
        elif user_type == 'verified':
            queryset = queryset.filter(is_verified=True)
        elif user_type == 'complete_profiles':
            queryset = queryset.filter(profile__is_complete=True)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['user_type'] = self.request.GET.get('user_type', '')
        return context


@user_passes_test(is_superuser)
def user_detail(request, user_id):
    """Detailed view of a specific user"""
    user = get_object_or_404(User, id=user_id)
    
    # Get user statistics
    likes_given = Like.objects.filter(from_user=user).count()
    likes_received = Like.objects.filter(to_user=user).count()
    matches = Match.objects.filter(Q(user1=user) | Q(user2=user)).count() if Match else 0
    notifications_sent = Notification.objects.filter(sender=user).count()
    notifications_received = Notification.objects.filter(receiver=user).count()
    purchases = Purchase.objects.filter(user=user).count() if Purchase else 0
    
    # Recent activity
    recent_likes = Like.objects.filter(from_user=user).select_related('to_user').order_by('-created_at')[:5]
    recent_notifications = Notification.objects.filter(
        receiver=user
    ).select_related('sender').order_by('-created_at')[:5]
    
    context = {
        'user_obj': user,  # Renamed to avoid conflict with request.user
        'likes_given': likes_given,
        'likes_received': likes_received,
        'matches': matches,
        'notifications_sent': notifications_sent,
        'notifications_received': notifications_received,
        'purchases': purchases,
        'recent_likes': recent_likes,
        'recent_notifications': recent_notifications,
    }
    
    return render(request, 'admin_dashboard/user_detail.html', context)


@user_passes_test(is_superuser)
def delete_user_profile(request, user_id):
    """Delete a user's profile (soft delete by deactivating)"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'deactivate':
            user.is_active = False
            user.save()
            messages.success(request, f'User {user.username} has been deactivated.')
        elif action == 'delete_profile':
            if hasattr(user, 'profile'):
                user.profile.delete()
            messages.success(request, f'Profile for {user.username} has been deleted.')
        elif action == 'delete_user':
            username = user.username
            user.delete()
            messages.success(request, f'User {username} has been completely deleted.')
            return redirect('admin_dashboard:user_management')
        
        return redirect('admin_dashboard:user_detail', user_id=user_id)
    
    return render(request, 'admin_dashboard/confirm_delete.html', {'user_obj': user})


@user_passes_test(is_superuser)
def platform_analytics(request):
    """Comprehensive platform analytics and insights"""
    from django.db.models import Avg, Sum, Max, Min, F, ExpressionWrapper, fields as dj_fields
    from datetime import date
    from decimal import Decimal

    # Get date range from request
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    today = timezone.now()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # ===== 1. USER ANALYTICS =====
    total_users = User.objects.count()
    new_users_period = User.objects.filter(date_joined__gte=start_date).count()

    # Daily/Weekly/Monthly Active Users
    dau = User.objects.filter(last_login__gte=today - timedelta(days=1)).count()
    wau = User.objects.filter(last_login__gte=week_ago).count()
    mau = User.objects.filter(last_login__gte=month_ago).count()

    # Retention Rate (Day 1, 7, 30)
    day1_cohort = User.objects.filter(date_joined__gte=today - timedelta(days=2), date_joined__lt=today - timedelta(days=1))
    day1_retained = day1_cohort.filter(last_login__gte=today - timedelta(days=1)).count()
    day1_retention = round((day1_retained / day1_cohort.count() * 100) if day1_cohort.count() > 0 else 0, 2)

    day7_cohort = User.objects.filter(date_joined__gte=today - timedelta(days=14), date_joined__lt=today - timedelta(days=7))
    day7_retained = day7_cohort.filter(last_login__gte=week_ago).count()
    day7_retention = round((day7_retained / day7_cohort.count() * 100) if day7_cohort.count() > 0 else 0, 2)

    day30_cohort = User.objects.filter(date_joined__gte=today - timedelta(days=60), date_joined__lt=month_ago)
    day30_retained = day30_cohort.filter(last_login__gte=month_ago).count()
    day30_retention = round((day30_retained / day30_cohort.count() * 100) if day30_cohort.count() > 0 else 0, 2)

    # Churn Rate (users who haven't logged in for 30+ days)
    churned_users = User.objects.filter(last_login__lt=month_ago).count()
    churn_rate = round((churned_users / total_users * 100) if total_users > 0 else 0, 2)

    # User demographics
    students_count = User.objects.filter(is_student=True).count()
    verified_count = User.objects.filter(is_verified=True).count()
    country_distribution = User.objects.values('country').annotate(count=Count('id')).order_by('-count')[:10]

    # Gender distribution
    gender_distribution = Profile.objects.exclude(gender='').values('gender').annotate(count=Count('id')).order_by('-count')

    # Study year distribution
    study_year_distribution = Profile.objects.exclude(study_year__isnull=True).values('study_year').annotate(count=Count('id')).order_by('study_year')

    # Age distribution (calculated from birth_date)
    from django.db.models.functions import ExtractYear
    age_ranges = {
        '18-22': User.objects.filter(profile__birth_date__gte=today - timedelta(days=365*22), profile__birth_date__lt=today - timedelta(days=365*18)).count(),
        '23-27': User.objects.filter(profile__birth_date__gte=today - timedelta(days=365*27), profile__birth_date__lt=today - timedelta(days=365*23)).count(),
        '28-32': User.objects.filter(profile__birth_date__gte=today - timedelta(days=365*32), profile__birth_date__lt=today - timedelta(days=365*28)).count(),
        '33+': User.objects.filter(profile__birth_date__lt=today - timedelta(days=365*33)).count(),
    }

    # School/University distribution (top 10)
    university_distribution = Profile.objects.exclude(school_name='').values('school_name').annotate(
        count=Count('id')
    ).order_by('-count')[:10]

    # Referral analytics
    referred_users = User.objects.filter(referred_by__isnull=False).count()
    organic_users = total_users - referred_users

    # User registrations over time
    from django.db.models.functions import TruncDate
    user_registrations = User.objects.filter(
        date_joined__gte=start_date
    ).annotate(
        day=TruncDate('date_joined')
    ).values('day').annotate(count=Count('id')).order_by('day')

    # ===== 2. PROFILE ANALYTICS =====
    total_profiles = Profile.objects.count()
    complete_profiles = Profile.objects.filter(is_complete=True).count()
    incomplete_profiles = total_profiles - complete_profiles
    profiles_with_photos = Profile.objects.exclude(profile_picture='').count()
    completion_rate = round((complete_profiles / total_profiles * 100) if total_profiles > 0 else 0, 2)

    # Average time to complete profile (users who completed within 7 days)
    completed_with_time = User.objects.filter(
        profile__is_complete=True,
        profile__updated_at__isnull=False
    ).annotate(
        completion_time=ExpressionWrapper(
            F('profile__updated_at') - F('date_joined'),
            output_field=dj_fields.DurationField()
        )
    )
    avg_completion_time_seconds = completed_with_time.aggregate(avg=Avg('completion_time'))['avg']
    avg_completion_hours = round(avg_completion_time_seconds.total_seconds() / 3600, 2) if avg_completion_time_seconds else 0

    # Profile abandonment rate (incomplete profiles > 7 days old)
    old_incomplete = Profile.objects.filter(
        is_complete=False,
        user__date_joined__lt=today - timedelta(days=7)
    ).count()
    abandonment_rate = round((old_incomplete / total_profiles * 100) if total_profiles > 0 else 0, 2)

    # Popular interests (top 20)
    all_interests = []
    for profile in Profile.objects.exclude(interests=''):
        interests_list = [i.strip() for i in profile.interests.split(',') if i.strip()]
        all_interests.extend(interests_list)

    from collections import Counter
    interest_counts = Counter(all_interests)
    popular_interests = [{'interest': k, 'count': v} for k, v in interest_counts.most_common(20)]

    # Study field distribution
    popular_fields = Profile.objects.exclude(study_field='').values('study_field').annotate(
        count=Count('id')
    ).order_by('-count')[:10]

    # ===== 3. LIKE/UNLIKE ANALYTICS =====
    total_likes = Like.objects.count()
    mutual_likes = Like.objects.filter(is_mutual=True).count()

    total_unlikes = Unlike.objects.count()

    # Like conversion rate (likes that became mutual)
    like_conversion_rate = round((mutual_likes / total_likes * 100) if total_likes > 0 else 0, 2)

    # Average time to mutual like (not tracked - no mutual_at field)
    avg_time_to_mutual_hours = 0  # Placeholder - field doesn't exist in model

    # Likes over time
    likes_over_time = Like.objects.filter(
        created_at__gte=start_date
    ).annotate(
        day=TruncDate('created_at')
    ).values('day').annotate(count=Count('id')).order_by('day')

    # Top liked users
    top_liked_users = User.objects.annotate(
        total_received=F('received_likes_count')
    ).order_by('-total_received')[:10]

    # Average likes per user
    avg_likes_sent = Like.objects.values('from_user').annotate(count=Count('id')).aggregate(avg=Avg('count'))['avg'] or 0
    avg_likes_received = round((total_likes / total_users) if total_users > 0 else 0, 2)

    # ===== 4. PAYMENT & REVENUE ANALYTICS =====
    if Purchase:
        total_purchases = Purchase.objects.count()
        completed_purchases = Purchase.objects.filter(status='completed')
        failed_purchases = Purchase.objects.filter(status='failed')
        total_revenue = completed_purchases.aggregate(total=Sum('amount'))['total'] or Decimal('0')

        # Revenue by provider
        paystack_revenue = completed_purchases.filter(payment_provider='paystack').aggregate(total=Sum('amount'))['total'] or Decimal('0')
        stripe_revenue = completed_purchases.filter(payment_provider='stripe').aggregate(total=Sum('amount'))['total'] or Decimal('0')

        # Revenue over time
        revenue_over_time = completed_purchases.filter(
            created_at__gte=start_date
        ).annotate(
            day=TruncDate('created_at')
        ).values('day').annotate(revenue=Sum('amount')).order_by('day')

        # Average order value
        aov = completed_purchases.aggregate(avg=Avg('amount'))['avg'] or Decimal('0')

        # Revenue per user (RPU)
        buyers_count = completed_purchases.values('user').distinct().count()
        rpu = round(float(total_revenue) / buyers_count, 2) if buyers_count > 0 else 0

        # Repeat purchase rate
        repeat_buyers = completed_purchases.values('user').annotate(
            purchase_count=Count('id')
        ).filter(purchase_count__gt=1).count()
        repeat_purchase_rate = round((repeat_buyers / buyers_count * 100) if buyers_count > 0 else 0, 2)

        # Failed transaction analysis
        failed_count = failed_purchases.count()
        failure_rate = round((failed_count / total_purchases * 100) if total_purchases > 0 else 0, 2)

        # Failed by provider
        paystack_failed = failed_purchases.filter(payment_provider='paystack').count()
        stripe_failed = failed_purchases.filter(payment_provider='stripe').count()

        # Conversion metrics
        conversion_rate = round((buyers_count / total_users * 100) if total_users > 0 else 0, 2)
    else:
        total_purchases = total_revenue = aov = rpu = 0
        revenue_over_time = []
        paystack_revenue = stripe_revenue = Decimal('0')
        conversion_rate = repeat_purchase_rate = failure_rate = 0
        failed_count = paystack_failed = stripe_failed = 0

    # ===== 5. QUIZ ANALYTICS =====
    total_questions = Question.objects.count()
    active_questions = Question.objects.filter(is_active=True).count()
    total_quiz_responses = UserQuizResponse.objects.count()
    correct_responses = UserQuizResponse.objects.filter(is_correct=True).count()
    quiz_accuracy = round((correct_responses / total_quiz_responses * 100) if total_quiz_responses > 0 else 0, 2)

    # Quiz participation rate
    users_participated = UserQuizResponse.objects.values('user').distinct().count()
    participation_rate = round((users_participated / total_users * 100) if total_users > 0 else 0, 2)

    # Quiz engagement by time of day
    from django.db.models.functions import ExtractHour
    quiz_by_hour = UserQuizResponse.objects.annotate(
        hour=ExtractHour('answered_at')
    ).values('hour').annotate(count=Count('id')).order_by('hour')

    # Quiz streaks (users with consecutive daily participation)
    # Simplified: count users who answered in last 3 consecutive days
    three_days_ago = today - timedelta(days=3)
    streak_users = UserQuizResponse.objects.filter(
        answered_at__gte=three_days_ago
    ).values('user').annotate(
        days_participated=Count('answered_at__date', distinct=True)
    ).filter(days_participated__gte=3).count()

    # Quiz engagement over time
    quiz_responses_over_time = UserQuizResponse.objects.filter(
        answered_at__gte=start_date
    ).annotate(
        day=TruncDate('answered_at')
    ).values('day').annotate(count=Count('id')).order_by('day')

    # Category popularity
    category_stats = Question.objects.values('category').annotate(
        total_questions=Count('id'),
        total_responses=Count('user_responses')
    ).order_by('-total_responses')

    # ===== 6. REFERRAL ANALYTICS =====
    try:
        from accounts.models import Referral
        total_referrals = Referral.objects.count()
        completed_referrals = Referral.objects.filter(status='completed').count()
        referral_conversion_rate = round((completed_referrals / total_referrals * 100) if total_referrals > 0 else 0, 2)
        total_referral_points = Referral.objects.filter(status='completed').aggregate(total=Sum('points_awarded'))['total'] or 0

        # Top referrers
        top_referrers = User.objects.annotate(
            referral_count=Count('referral_activities', filter=Q(referral_activities__status='completed'))
        ).filter(referral_count__gt=0).order_by('-referral_count')[:10]
    except ImportError:
        total_referrals = completed_referrals = referral_conversion_rate = total_referral_points = 0
        top_referrers = []

    # ===== 8. REWARDS ANALYTICS =====
    try:
        from rewards.models import Reward, RewardClaim
        total_rewards = Reward.objects.count()
        active_rewards = Reward.objects.filter(is_active=True).count()
        total_claims = RewardClaim.objects.count()

        # Points circulation
        total_points_in_system = User.objects.aggregate(total=Sum('points_balance'))['total'] or 0
        total_points_spent = RewardClaim.objects.aggregate(total=Sum('points_spent'))['total'] or 0

        # Popular rewards
        popular_rewards = Reward.objects.annotate(
            claim_count=Count('rewards_claims')
        ).order_by('-claim_count')[:5]
    except ImportError:
        total_rewards = active_rewards = total_claims = 0
        total_points_in_system = total_points_spent = 0
        popular_rewards = []

    # ===== 9. GEOGRAPHIC ANALYTICS =====
    users_by_country = User.objects.exclude(country='').values('country').annotate(
        count=Count('id')
    ).order_by('-count')

    # City distribution (top 10)
    users_by_city = Profile.objects.exclude(city='').values('city').annotate(
        count=Count('id')
    ).order_by('-count')[:10]

    # ===== 10. FUNNEL ANALYSIS =====
    # Registration → Profile Completion → First Like → Purchase
    funnel_registered = total_users
    funnel_profile_complete = complete_profiles
    funnel_first_like = User.objects.filter(likes_given__isnull=False).distinct().count()
    funnel_purchased = Purchase.objects.values('user').distinct().count() if Purchase else 0

    funnel_profile_rate = round((funnel_profile_complete / funnel_registered * 100) if funnel_registered > 0 else 0, 2)
    funnel_like_rate = round((funnel_first_like / funnel_profile_complete * 100) if funnel_profile_complete > 0 else 0, 2)
    funnel_purchase_rate = round((funnel_purchased / funnel_first_like * 100) if funnel_first_like > 0 else 0, 2)

    # ===== 11. COMPARATIVE & TREND ANALYTICS =====
    # Week-over-week growth
    users_this_week = User.objects.filter(date_joined__gte=week_ago).count()
    users_last_week = User.objects.filter(
        date_joined__gte=week_ago - timedelta(days=7),
        date_joined__lt=week_ago
    ).count()
    wow_growth = round(((users_this_week - users_last_week) / users_last_week * 100) if users_last_week > 0 else 0, 2)

    # Month-over-month growth
    users_this_month = User.objects.filter(date_joined__gte=month_ago).count()
    users_last_month = User.objects.filter(
        date_joined__gte=month_ago - timedelta(days=30),
        date_joined__lt=month_ago
    ).count()
    mom_growth = round(((users_this_month - users_last_month) / users_last_month * 100) if users_last_month > 0 else 0, 2)

    # ===== 12. UPDATES ANALYTICS =====
    try:
        from updates.models import Update
        total_updates = Update.objects.count()
        recent_updates = Update.objects.filter(created_at__gte=start_date).count()
    except:
        total_updates = recent_updates = 0

    # ===== 13. ADVERTISEMENT ANALYTICS =====
    try:
        from advertisements.models import Advertisement
        total_ads = Advertisement.objects.count()
        active_ads = Advertisement.objects.filter(is_active=True).count()
    except:
        total_ads = active_ads = 0

    # ===== 10. CONTENT & DISCOVERY ANALYTICS =====
    # Profile views (if tracked - placeholder for now)
    # Calculate percentage of profiles with photos
    profiles_with_photos_count = Profile.objects.exclude(profile_picture='').count()
    avg_profile_completeness = round((profiles_with_photos_count / total_profiles * 100) if total_profiles > 0 else 0, 2)

    context = {
        'days': days,

        # User Analytics
        'total_users': total_users,
        'new_users_period': new_users_period,
        'dau': dau,
        'wau': wau,
        'mau': mau,
        'day1_retention': day1_retention,
        'day7_retention': day7_retention,
        'day30_retention': day30_retention,
        'churn_rate': churn_rate,
        'students_count': students_count,
        'verified_count': verified_count,
        'country_distribution': country_distribution,
        'gender_distribution': gender_distribution,
        'study_year_distribution': study_year_distribution,
        'age_ranges': age_ranges,
        'university_distribution': university_distribution,
        'referred_users': referred_users,
        'organic_users': organic_users,
        'user_registrations': list(user_registrations),

        # Profile Analytics
        'total_profiles': total_profiles,
        'complete_profiles': complete_profiles,
        'incomplete_profiles': incomplete_profiles,
        'profiles_with_photos': profiles_with_photos,
        'completion_rate': completion_rate,
        'avg_completion_hours': avg_completion_hours,
        'abandonment_rate': abandonment_rate,
        'popular_interests': popular_interests,
        'popular_fields': popular_fields,

        # Like/Unlike Analytics
        'total_likes': total_likes,
        'mutual_likes': mutual_likes,
        'total_unlikes': total_unlikes,
        'like_conversion_rate': like_conversion_rate,
        'avg_time_to_mutual_hours': avg_time_to_mutual_hours,
        'likes_over_time': list(likes_over_time),
        'top_liked_users': top_liked_users,
        'avg_likes_sent': round(avg_likes_sent, 2),
        'avg_likes_received': avg_likes_received,

        # Payment Analytics
        'total_purchases': total_purchases,
        'total_revenue': total_revenue,
        'paystack_revenue': paystack_revenue,
        'stripe_revenue': stripe_revenue,
        'revenue_over_time': list(revenue_over_time),
        'aov': aov,
        'rpu': rpu,
        'repeat_purchase_rate': repeat_purchase_rate,
        'failure_rate': failure_rate,
        'failed_count': failed_count,
        'paystack_failed': paystack_failed,
        'stripe_failed': stripe_failed,
        'conversion_rate': conversion_rate,

        # Quiz Analytics
        'total_questions': total_questions,
        'active_questions': active_questions,
        'total_quiz_responses': total_quiz_responses,
        'quiz_accuracy': quiz_accuracy,
        'participation_rate': participation_rate,
        'quiz_by_hour': list(quiz_by_hour),
        'streak_users': streak_users,
        'quiz_responses_over_time': list(quiz_responses_over_time),
        'category_stats': category_stats,

        # Referral Analytics
        'total_referrals': total_referrals,
        'completed_referrals': completed_referrals,
        'referral_conversion_rate': referral_conversion_rate,
        'total_referral_points': total_referral_points,
        'top_referrers': top_referrers,

        # Rewards Analytics
        'total_rewards': total_rewards,
        'active_rewards': active_rewards,
        'total_claims': total_claims,
        'total_points_in_system': total_points_in_system,
        'total_points_spent': total_points_spent,
        'popular_rewards': popular_rewards,

        # Geographic Analytics
        'users_by_country': users_by_country,
        'users_by_city': users_by_city,

        # Funnel Analytics
        'funnel_registered': funnel_registered,
        'funnel_profile_complete': funnel_profile_complete,
        'funnel_first_like': funnel_first_like,
        'funnel_purchased': funnel_purchased,
        'funnel_profile_rate': funnel_profile_rate,
        'funnel_like_rate': funnel_like_rate,
        'funnel_purchase_rate': funnel_purchase_rate,

        # Trend Analytics
        'wow_growth': wow_growth,
        'mom_growth': mom_growth,

        # Content Analytics
        'total_updates': total_updates,
        'recent_updates': recent_updates,
        'total_ads': total_ads,
        'active_ads': active_ads,
    }

    return render(request, 'admin_dashboard/analytics.html', context)


@user_passes_test(is_superuser)
def export_data(request):
    """Export platform data"""
    import csv
    from django.http import HttpResponse
    
    export_type = request.GET.get('type', 'users')
    
    response = HttpResponse(content_type='text/csv')
    
    if export_type == 'users':
        response['Content-Disposition'] = 'attachment; filename="users.csv"'
        writer = csv.writer(response)
        writer.writerow(['Username', 'Email', 'Date Joined', 'Is Student', 'Is Verified', 'Profile Complete'])
        
        users = User.objects.select_related('profile').all()
        for user in users:
            writer.writerow([
                user.username,
                user.email,
                user.date_joined.strftime('%Y-%m-%d'),
                user.is_student,
                user.is_verified,
                hasattr(user, 'profile') and user.profile.is_complete
            ])
    
    elif export_type == 'matches' and Match:
        response['Content-Disposition'] = 'attachment; filename="matches.csv"'
        writer = csv.writer(response)
        writer.writerow(['User 1', 'User 2', 'Match Date'])

        matches = Match.objects.select_related('user1', 'user2').all()
        for match in matches:
            writer.writerow([
                match.user1.username,
                match.user2.username,
                match.created_at.strftime('%Y-%m-%d %H:%M')
            ])
    
    return response


@user_passes_test(is_superuser)
def quiz_management(request):
    """Quiz management dashboard for admins"""
    
    # Quiz statistics
    total_questions = Question.objects.count()
    active_questions = Question.objects.filter(is_active=True).count()
    total_responses = UserQuizResponse.objects.count()
    correct_responses = UserQuizResponse.objects.filter(is_correct=True).count()
    
    # Category statistics
    category_stats = Question.objects.values('category').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Difficulty statistics
    difficulty_stats = Question.objects.values('difficulty').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Recent questions
    recent_questions = Question.objects.select_related('created_by').order_by('-created_at')[:10]
    
    # Daily quiz stats
    today = timezone.now().date()
    daily_quiz_today = DailyQuiz.objects.filter(date=today).first()
    
    # Response rate over last 7 days
    week_ago = today - timedelta(days=7)
    weekly_responses = UserQuizResponse.objects.filter(
        answered_at__gte=week_ago
    ).annotate(
        day=TruncDate('answered_at')
    ).values('day').annotate(
        count=Count('id'),
        correct=Count('id', filter=Q(is_correct=True))
    ).order_by('day')
    
    # Top performing questions (highest accuracy)
    top_questions = Question.objects.annotate(
        total_responses=Count('user_responses'),
        correct_responses=Count('user_responses', filter=Q(user_responses__is_correct=True))
    ).filter(total_responses__gt=0).extra(
        select={'accuracy': 'CASE WHEN total_responses > 0 THEN (correct_responses * 100.0 / total_responses) ELSE 0 END'}
    ).order_by('-accuracy')[:5]
    
    context = {
        'total_questions': total_questions,
        'active_questions': active_questions,
        'total_responses': total_responses,
        'correct_responses': correct_responses,
        'accuracy_rate': round((correct_responses / total_responses * 100) if total_responses > 0 else 0, 2),
        'category_stats': category_stats,
        'difficulty_stats': difficulty_stats,
        'recent_questions': recent_questions,
        'daily_quiz_today': daily_quiz_today,
        'weekly_responses': list(weekly_responses),
        'top_questions': top_questions,
    }
    
    return render(request, 'admin_dashboard/quiz_management.html', context)


@user_passes_test(is_superuser)
def create_question(request):
    """Create a new quiz question"""
    if request.method == 'POST':
        try:
            # Get form data
            question_text = request.POST.get('question_text', '').strip()
            category = request.POST.get('category', 'general')
            difficulty = request.POST.get('difficulty', 'medium')
            points_value = int(request.POST.get('points_value', 1))
            
            # Get choices
            choices_data = []
            correct_choice_index = int(request.POST.get('correct_choice', 0))
            
            for i in range(4):  # 4 choices
                choice_text = request.POST.get(f'choice_{i}', '').strip()
                if choice_text:
                    choices_data.append({
                        'text': choice_text,
                        'is_correct': i == correct_choice_index,
                        'order': i + 1
                    })
            
            # Validation
            if not question_text:
                messages.error(request, 'Question text is required.')
                return redirect('admin_dashboard:quiz_management')
            
            if len(choices_data) < 2:
                messages.error(request, 'At least 2 choices are required.')
                return redirect('admin_dashboard:quiz_management')
            
            # Create question
            question = Question.objects.create(
                text=question_text,
                category=category,
                difficulty=difficulty,
                points_value=points_value,
                created_by=request.user
            )
            
            # Create choices
            for choice_data in choices_data:
                Choice.objects.create(
                    question=question,
                    text=choice_data['text'],
                    is_correct=choice_data['is_correct'],
                    order=choice_data['order']
                )
            
            messages.success(request, f'Question "{question_text[:50]}..." created successfully!')
            
        except Exception as e:
            messages.error(request, f'Error creating question: {str(e)}')
    
    return redirect('admin_dashboard:quiz_management')


@user_passes_test(is_superuser)
def delete_question(request, question_id):
    """Delete a quiz question"""
    question = get_object_or_404(Question, id=question_id)
    
    if request.method == 'POST':
        question_text = question.text[:50]
        question.delete()
        messages.success(request, f'Question "{question_text}..." deleted successfully!')
    
    return redirect('admin_dashboard:quiz_management')


@user_passes_test(is_superuser)
def toggle_question_status(request, question_id):
    """Toggle question active/inactive status"""
    question = get_object_or_404(Question, id=question_id)
    question.is_active = not question.is_active
    question.save()
    
    status = "activated" if question.is_active else "deactivated"
    messages.success(request, f'Question "{question.text[:50]}..." {status}!')
    
    return redirect('admin_dashboard:quiz_management')


@user_passes_test(is_superuser)
def set_daily_quiz(request, question_id):
    """Set a specific question as today's daily quiz"""
    question = get_object_or_404(Question, id=question_id, is_active=True)
    today = timezone.now().date()

    # Remove existing daily quiz for today
    DailyQuiz.objects.filter(date=today).delete()

    # Create new daily quiz
    DailyQuiz.objects.create(question=question, date=today)

    messages.success(request, f'Question "{question.text[:50]}..." set as today\'s daily quiz!')
    return redirect('admin_dashboard:quiz_management')


@user_passes_test(is_superuser)
def question_detail(request, question_id):
    """View detailed statistics for a specific question including users who got it right/wrong"""
    question = get_object_or_404(Question, id=question_id)

    # Get all responses for this question
    all_responses = UserQuizResponse.objects.filter(
        question=question
    ).select_related('user', 'selected_choice').order_by('-answered_at')

    # Separate correct and incorrect responses
    correct_responses = all_responses.filter(is_correct=True)
    incorrect_responses = all_responses.filter(is_correct=False)

    # Calculate statistics
    total_responses = all_responses.count()
    total_correct = correct_responses.count()
    total_incorrect = incorrect_responses.count()
    accuracy = round((total_correct / total_responses * 100) if total_responses > 0 else 0, 2)

    # Get choice statistics
    choice_stats = []
    for choice in question.choices.all().order_by('order'):
        choice_count = all_responses.filter(selected_choice=choice).count()
        choice_percentage = round((choice_count / total_responses * 100) if total_responses > 0 else 0, 2)
        choice_stats.append({
            'choice': choice,
            'count': choice_count,
            'percentage': choice_percentage,
            'is_correct': choice.is_correct
        })

    # Check if this is the daily quiz
    today = timezone.now().date()
    is_daily_quiz = DailyQuiz.objects.filter(question=question, date=today).exists()

    context = {
        'question': question,
        'total_responses': total_responses,
        'total_correct': total_correct,
        'total_incorrect': total_incorrect,
        'accuracy': accuracy,
        'correct_responses': correct_responses,
        'incorrect_responses': incorrect_responses,
        'choice_stats': choice_stats,
        'is_daily_quiz': is_daily_quiz,
    }

    return render(request, 'admin_dashboard/question_detail.html', context)


@user_passes_test(is_superuser)
def generate_questions(request):
    """Generate quiz questions using Open Trivia Database API"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

    try:
        import json
        import requests
        import html

        data = json.loads(request.body)
        category = data.get('category', 'general')
        difficulty = data.get('difficulty', 'medium')
        count = min(int(data.get('count', 5)), 10)  # Max 10 questions

        # Map our categories to Open Trivia DB categories
        category_map = {
            'general': 9,      # General Knowledge
            'science': 17,     # Science & Nature
            'history': 23,     # History
            'sports': 21,      # Sports
            'entertainment': 11,  # Film
            'geography': 22,   # Geography
            'literature': 10,  # Books
            'technology': 18,  # Computers
        }

        trivia_category = category_map.get(category, 9)

        # Fetch questions from Open Trivia Database
        url = f'https://opentdb.com/api.php?amount={count}&category={trivia_category}&difficulty={difficulty}&type=multiple'

        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            return JsonResponse({'success': False, 'error': 'Failed to fetch questions from API'})

        trivia_data = response.json()

        if trivia_data['response_code'] != 0:
            return JsonResponse({'success': False, 'error': 'No questions available for this category/difficulty'})

        created_count = 0

        for item in trivia_data['results']:
            # Decode HTML entities
            question_text = html.unescape(item['question'])
            correct_answer = html.unescape(item['correct_answer'])
            incorrect_answers = [html.unescape(ans) for ans in item['incorrect_answers']]

            # All questions are worth 1 point regardless of difficulty
            points_value = 1

            # Create question
            question = Question.objects.create(
                text=question_text,
                category=category,
                difficulty=difficulty,
                points_value=points_value,
                created_by=request.user,
                is_active=True
            )

            # Shuffle answers
            all_answers = incorrect_answers + [correct_answer]
            import random
            random.shuffle(all_answers)

            # Create choices
            for i, answer in enumerate(all_answers):
                Choice.objects.create(
                    question=question,
                    text=answer,
                    is_correct=(answer == correct_answer),
                    order=i + 1
                )

            created_count += 1

        return JsonResponse({
            'success': True,
            'created_count': created_count,
            'message': f'Successfully created {created_count} questions'
        })

    except requests.exceptions.RequestException as e:
        return JsonResponse({'success': False, 'error': f'API request failed: {str(e)}'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ===== PAYMENT PACKAGES MANAGEMENT =====

@user_passes_test(is_superuser)
def packages_management(request):
    """Manage packages (unified package system)"""
    from payments.models import Package

    packages = Package.objects.all().order_by('-created_at')

    context = {
        'packages': packages,
    }

    return render(request, 'admin_dashboard/packages_management.html', context)


@user_passes_test(is_superuser)
def create_package(request):
    """Create a new package"""
    if request.method == 'POST':
        from payments.models import Package
        try:
            Package.objects.create(
                name=request.POST.get('name'),
                price=request.POST.get('price'),
                likes_count=request.POST.get('likes_count'),
                boosters=request.POST.get('boosters', 0),
                description=request.POST.get('description', ''),
                is_active=request.POST.get('is_active') == 'on'
            )
            messages.success(request, 'Package created successfully!')
        except Exception as e:
            messages.error(request, f'Error creating package: {str(e)}')

    return redirect('admin_dashboard:packages_management')


@user_passes_test(is_superuser)
def edit_package(request, package_id):
    """Edit a package"""
    from payments.models import Package
    package = get_object_or_404(Package, id=package_id)

    if request.method == 'POST':
        try:
            package.name = request.POST.get('name')
            package.price = request.POST.get('price')
            package.likes_count = request.POST.get('likes_count')
            package.boosters = request.POST.get('boosters', 0)
            package.description = request.POST.get('description', '')
            package.is_active = request.POST.get('is_active') == 'on'
            package.save()
            messages.success(request, 'Package updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating package: {str(e)}')
        return redirect('admin_dashboard:packages_management')

    return render(request, 'admin_dashboard/edit_package.html', {'package': package})


@user_passes_test(is_superuser)
def delete_package(request, package_id):
    """Delete a package"""
    from payments.models import Package
    package = get_object_or_404(Package, id=package_id)

    if request.method == 'POST':
        package_name = package.name
        package.delete()
        messages.success(request, f'Package "{package_name}" deleted successfully!')

    return redirect('admin_dashboard:packages_management')


# ===== PURCHASES MANAGEMENT =====

@user_passes_test(is_superuser)
def purchases_management(request):
    """View and manage all purchases"""
    from payments.models import Purchase

    # Filter by status
    status_filter = request.GET.get('status', '')
    provider_filter = request.GET.get('provider', '')
    search = request.GET.get('search', '').strip()

    purchases = Purchase.objects.select_related('user', 'package').order_by('-created_at')

    if status_filter:
        purchases = purchases.filter(status=status_filter)
    if provider_filter:
        purchases = purchases.filter(payment_provider=provider_filter)
    if search:
        purchases = purchases.filter(
            Q(user__username__icontains=search) |
            Q(user__email__icontains=search) |
            Q(paystack_reference__icontains=search) |
            Q(stripe_session_id__icontains=search)
        )

    # Pagination
    paginator = Paginator(purchases, 20)
    page = request.GET.get('page')
    purchases = paginator.get_page(page)

    context = {
        'purchases': purchases,
        'status_filter': status_filter,
        'provider_filter': provider_filter,
        'search': search,
    }

    return render(request, 'admin_dashboard/purchases_management.html', context)


@user_passes_test(is_superuser)
def purchase_detail(request, purchase_id):
    """View and manage a specific purchase"""
    from payments.models import Purchase
    purchase = get_object_or_404(Purchase, id=purchase_id)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'complete':
            purchase.status = 'completed'
            purchase.completed_at = timezone.now()
            purchase.save()
            messages.success(request, 'Purchase marked as completed!')

        elif action == 'fail':
            purchase.status = 'failed'
            purchase.save()
            messages.success(request, 'Purchase marked as failed!')

        elif action == 'refund':
            purchase.status = 'refunded'
            # Deduct the likes from user balance
            if purchase.package:
                purchase.user.likes_balance = max(0, purchase.user.likes_balance - purchase.package.likes_count)
            purchase.user.save()
            purchase.save()
            messages.success(request, 'Purchase refunded successfully!')

        return redirect('admin_dashboard:purchase_detail', purchase_id=purchase_id)

    context = {'purchase': purchase}
    return render(request, 'admin_dashboard/purchase_detail.html', context)


# ===== REWARDS MANAGEMENT =====

@user_passes_test(is_superuser)
def rewards_management(request):
    """Manage rewards"""
    from rewards.models import Reward

    rewards = Reward.objects.all().order_by('-created_at')

    context = {'rewards': rewards}
    return render(request, 'admin_dashboard/rewards_management.html', context)


@user_passes_test(is_superuser)
def create_reward(request):
    """Create a new reward"""
    from rewards.models import Reward

    if request.method == 'POST':
        try:
            reward = Reward.objects.create(
                name=request.POST.get('name'),
                description=request.POST.get('description'),
                points_cost=request.POST.get('points_cost'),
                reward_type=request.POST.get('reward_type'),
                stock_quantity=request.POST.get('stock_quantity', 0),
                is_active=request.POST.get('is_active') == 'on'
            )

            # Handle image upload
            if request.FILES.get('image'):
                reward.image = request.FILES['image']
                reward.save()

            messages.success(request, 'Reward created successfully!')
        except Exception as e:
            messages.error(request, f'Error creating reward: {str(e)}')

        return redirect('admin_dashboard:rewards_management')

    from rewards.models import Reward
    reward_types = Reward.REWARD_TYPES
    return render(request, 'admin_dashboard/create_reward.html', {'reward_types': reward_types})


@user_passes_test(is_superuser)
def edit_reward(request, reward_id):
    """Edit a reward"""
    from rewards.models import Reward
    reward = get_object_or_404(Reward, id=reward_id)

    if request.method == 'POST':
        try:
            reward.name = request.POST.get('name')
            reward.description = request.POST.get('description')
            reward.points_cost = request.POST.get('points_cost')
            reward.reward_type = request.POST.get('reward_type')
            reward.stock_quantity = request.POST.get('stock_quantity', 0)
            reward.is_active = request.POST.get('is_active') == 'on'

            # Handle image upload
            if request.FILES.get('image'):
                reward.image = request.FILES['image']

            reward.save()
            messages.success(request, 'Reward updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating reward: {str(e)}')

        return redirect('admin_dashboard:rewards_management')

    from rewards.models import Reward
    reward_types = Reward.REWARD_TYPES
    context = {'reward': reward, 'reward_types': reward_types}
    return render(request, 'admin_dashboard/edit_reward.html', context)


@user_passes_test(is_superuser)
def delete_reward(request, reward_id):
    """Delete a reward"""
    from rewards.models import Reward
    reward = get_object_or_404(Reward, id=reward_id)

    if request.method == 'POST':
        reward_name = reward.name
        reward.delete()
        messages.success(request, f'Reward "{reward_name}" deleted successfully!')

    return redirect('admin_dashboard:rewards_management')


@user_passes_test(is_superuser)
def toggle_reward_status(request, reward_id):
    """Toggle reward active status"""
    from rewards.models import Reward
    reward = get_object_or_404(Reward, id=reward_id)

    reward.is_active = not reward.is_active
    reward.save()

    status = "activated" if reward.is_active else "deactivated"
    messages.success(request, f'Reward "{reward.name}" {status}!')

    return redirect('admin_dashboard:rewards_management')


# ===== REWARD CLAIMS MANAGEMENT =====

@user_passes_test(is_superuser)
def reward_claims_management(request):
    """Manage reward claims"""
    from rewards.models import RewardClaim

    # Filter by status
    status_filter = request.GET.get('status', '')
    claims = RewardClaim.objects.select_related('user', 'reward').order_by('-claimed_at')

    if status_filter:
        claims = claims.filter(status=status_filter)

    # Pagination
    paginator = Paginator(claims, 20)
    page = request.GET.get('page')
    claims = paginator.get_page(page)

    from rewards.models import RewardClaim
    status_choices = RewardClaim.STATUS_CHOICES

    context = {
        'claims': claims,
        'status_filter': status_filter,
        'status_choices': status_choices,
    }

    return render(request, 'admin_dashboard/reward_claims_management.html', context)


@user_passes_test(is_superuser)
def update_reward_claim_status(request, claim_id):
    """Update reward claim status"""
    from rewards.models import RewardClaim
    claim = get_object_or_404(RewardClaim, id=claim_id)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        claim.status = new_status
        claim.save()
        messages.success(request, f'Claim status updated to {new_status}!')

    return redirect('admin_dashboard:reward_claims')


# ===== ADVERTISEMENTS MANAGEMENT =====

@user_passes_test(is_superuser)
def advertisements_management(request):
    """Manage advertisements"""
    from advertisements.models import Advertisement

    advertisements = Advertisement.objects.all().order_by('-display_priority', '-created_at')

    context = {'advertisements': advertisements}
    return render(request, 'admin_dashboard/advertisements_management.html', context)


@user_passes_test(is_superuser)
def create_advertisement(request):
    """Create a new advertisement"""
    from advertisements.models import Advertisement

    if request.method == 'POST':
        try:
            ad = Advertisement.objects.create(
                brand_name=request.POST.get('brand_name'),
                description=request.POST.get('description', ''),
                brand_url=request.POST.get('brand_url', ''),
                display_priority=request.POST.get('display_priority', 1),
                is_active=request.POST.get('is_active') == 'on'
            )

            # Handle image upload
            if request.FILES.get('flyer_image'):
                ad.flyer_image = request.FILES['flyer_image']
                ad.save()

            messages.success(request, 'Advertisement created successfully!')
        except Exception as e:
            messages.error(request, f'Error creating advertisement: {str(e)}')

        return redirect('admin_dashboard:advertisements_management')

    return render(request, 'admin_dashboard/create_advertisement.html')


@user_passes_test(is_superuser)
def edit_advertisement(request, ad_id):
    """Edit an advertisement"""
    from advertisements.models import Advertisement
    ad = get_object_or_404(Advertisement, id=ad_id)

    if request.method == 'POST':
        try:
            ad.brand_name = request.POST.get('brand_name')
            ad.description = request.POST.get('description', '')
            ad.brand_url = request.POST.get('brand_url', '')
            ad.display_priority = request.POST.get('display_priority', 1)
            ad.is_active = request.POST.get('is_active') == 'on'

            # Handle image upload
            if request.FILES.get('flyer_image'):
                ad.flyer_image = request.FILES['flyer_image']

            ad.save()
            messages.success(request, 'Advertisement updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating advertisement: {str(e)}')

        return redirect('admin_dashboard:advertisements_management')

    context = {'ad': ad}
    return render(request, 'admin_dashboard/edit_advertisement.html', context)


@user_passes_test(is_superuser)
def delete_advertisement(request, ad_id):
    """Delete an advertisement"""
    from advertisements.models import Advertisement
    ad = get_object_or_404(Advertisement, id=ad_id)

    if request.method == 'POST':
        brand_name = ad.brand_name
        ad.delete()
        messages.success(request, f'Advertisement "{brand_name}" deleted successfully!')

    return redirect('admin_dashboard:advertisements_management')


@user_passes_test(is_superuser)
def toggle_advertisement_status(request, ad_id):
    """Toggle advertisement active status"""
    from advertisements.models import Advertisement
    ad = get_object_or_404(Advertisement, id=ad_id)

    ad.is_active = not ad.is_active
    ad.save()

    status = "activated" if ad.is_active else "deactivated"
    messages.success(request, f'Advertisement "{ad.brand_name}" {status}!')

    return redirect('admin_dashboard:advertisements_management')


# ===== REFERRALS MANAGEMENT =====

@user_passes_test(is_superuser)
def referrals_management(request):
    """View and manage referrals"""
    from accounts.models import Referral

    # Filter by status
    status_filter = request.GET.get('status', '')
    referrals = Referral.objects.select_related('referrer', 'referred_user').order_by('-created_at')

    if status_filter:
        referrals = referrals.filter(status=status_filter)

    # Pagination
    paginator = Paginator(referrals, 20)
    page = request.GET.get('page')
    referrals = paginator.get_page(page)

    # Top referrers
    top_referrers = User.objects.annotate(
        referral_count=Count('referral_activities', filter=Q(referral_activities__status='completed'))
    ).filter(referral_count__gt=0).order_by('-referral_count')[:10]

    from accounts.models import Referral
    status_choices = Referral.STATUS_CHOICES

    context = {
        'referrals': referrals,
        'top_referrers': top_referrers,
        'status_filter': status_filter,
        'status_choices': status_choices,
    }

    return render(request, 'admin_dashboard/referrals_management.html', context)


# ===== PROFILE MANAGEMENT =====

@user_passes_test(is_superuser)
def edit_profile(request, user_id):
    """Edit a user's profile"""
    user = get_object_or_404(User, id=user_id)
    profile = user.profile

    if request.method == 'POST':
        try:
            # Update user fields
            user.username = request.POST.get('username')
            user.email = request.POST.get('email')
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.is_student = request.POST.get('is_student') == 'on'
            user.is_verified = request.POST.get('is_verified') == 'on'
            user.country = request.POST.get('country', '')
            user.save()

            # Update profile fields
            profile.bio = request.POST.get('bio', '')
            profile.gender = request.POST.get('gender', '')
            profile.study_field = request.POST.get('study_field', '')

            study_year = request.POST.get('study_year', '')
            profile.study_year = int(study_year) if study_year else None

            profile.school_name = request.POST.get('school_name', '')
            profile.interests = request.POST.get('interests', '')
            profile.city = request.POST.get('city', '')
            profile.location = request.POST.get('location', '')

            # Handle birth date
            birth_date = request.POST.get('birth_date', '')
            if birth_date:
                from datetime import datetime
                profile.birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()

            # Handle profile picture
            if request.FILES.get('profile_picture'):
                profile.profile_picture = request.FILES['profile_picture']

            profile.save()
            messages.success(request, f'Profile for {user.username} updated successfully!')
            return redirect('admin_dashboard:user_detail', user_id=user_id)

        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')

    context = {
        'user_obj': user,
        'profile': profile,
    }
    return render(request, 'admin_dashboard/edit_profile.html', context)
