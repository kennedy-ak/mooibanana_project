# admin_dashboard/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.db.models import Count, Q
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
from likes.models import Like
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
            total=Count('amount')
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
    """Platform analytics and insights"""
    
    # Get date range from request
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # User registration over time
    user_registrations = User.objects.filter(
        date_joined__gte=start_date
    ).extra(
        select={'day': 'date(date_joined)'}
    ).values('day').annotate(count=Count('id')).order_by('day')
    
    # Matches over time
    if Match:
        matches_over_time = Match.objects.filter(
            created_at__gte=start_date
        ).extra(
            select={'day': 'date(created_at)'}
        ).values('day').annotate(count=Count('id')).order_by('day')
    else:
        matches_over_time = []
    
    # Most popular study fields
    popular_fields = Profile.objects.values('study_field').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # User engagement metrics
    active_users = User.objects.filter(
        last_login__gte=start_date
    ).count()
    
    context = {
        'days': days,
        'user_registrations': list(user_registrations),
        'matches_over_time': list(matches_over_time),
        'popular_fields': popular_fields,
        'active_users': active_users,
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
    ).extra(
        select={'day': 'date(answered_at)'}
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
