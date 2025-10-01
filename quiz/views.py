from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Sum
from .models import Question, Choice, UserQuizResponse, DailyQuiz
import json

@login_required
def get_daily_quiz(request):
    today = timezone.now().date()
    
    try:
        daily_quiz = DailyQuiz.objects.get(date=today)
        question = daily_quiz.question
    except DailyQuiz.DoesNotExist:
        active_questions = Question.objects.filter(is_active=True)
        if not active_questions.exists():
            return JsonResponse({'error': 'No questions available'}, status=404)
        
        question = active_questions.order_by('?').first()
        daily_quiz = DailyQuiz.objects.create(question=question, date=today)
    
    user_has_answered = UserQuizResponse.objects.filter(
        user=request.user, 
        question=question
    ).exists()
    
    if user_has_answered:
        response = UserQuizResponse.objects.get(user=request.user, question=question)
        return JsonResponse({
            'already_answered': True,
            'question_id': question.id,
            'question': question.text,
            'category': question.get_category_display(),
            'difficulty': question.get_difficulty_display(),
            'points_value': question.points_value,
            'choices': [
                {'id': choice.id, 'text': choice.text, 'order': choice.order}
                for choice in question.choices.all().order_by('order')
            ],
            'user_choice': response.selected_choice.text,
            'correct_choice': question.choices.get(is_correct=True).text,
            'is_correct': response.is_correct,
            'points_earned': response.points_earned,
            'accuracy': daily_quiz.accuracy_percentage
        })
    
    choices_data = [
        {'id': choice.id, 'text': choice.text, 'order': choice.order}
        for choice in question.choices.all().order_by('order')
    ]
    
    return JsonResponse({
        'question_id': question.id,
        'question': question.text,
        'category': question.get_category_display(),
        'difficulty': question.get_difficulty_display(),
        'points_value': question.points_value,
        'choices': choices_data,
        'already_answered': False
    })

@login_required
@require_POST
def submit_quiz_answer(request):
    try:
        data = json.loads(request.body)
        question_id = data.get('question_id')
        choice_id = data.get('choice_id')
        
        if not question_id or not choice_id:
            return JsonResponse({'error': 'Missing question_id or choice_id'}, status=400)
        
        question = get_object_or_404(Question, id=question_id, is_active=True)
        choice = get_object_or_404(Choice, id=choice_id, question=question)
        
        if UserQuizResponse.objects.filter(user=request.user, question=question).exists():
            return JsonResponse({'error': 'You have already answered this question'}, status=400)
        
        response = UserQuizResponse.objects.create(
            user=request.user,
            question=question,
            selected_choice=choice
        )
        
        today = timezone.now().date()
        daily_quiz, created = DailyQuiz.objects.get_or_create(
            date=today,
            defaults={'question': question}
        )
        
        daily_quiz.total_responses += 1
        if response.is_correct:
            daily_quiz.correct_responses += 1
        daily_quiz.save()
        
        correct_choice = question.choices.get(is_correct=True)
        
        return JsonResponse({
            'success': True,
            'is_correct': response.is_correct,
            'points_earned': response.points_earned,
            'correct_choice': correct_choice.text,
            'user_choice': choice.text,
            'total_points': request.user.points_balance,
            'accuracy': daily_quiz.accuracy_percentage
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def quiz_stats(request):
    user_responses = UserQuizResponse.objects.filter(user=request.user)
    total_answered = user_responses.count()
    correct_answers = user_responses.filter(is_correct=True).count()
    total_points_from_quiz = user_responses.filter(is_correct=True).aggregate(
        total=Sum('points_earned')
    )['total'] or 0
    
    accuracy = round((correct_answers / total_answered) * 100, 2) if total_answered > 0 else 0
    
    return JsonResponse({
        'total_answered': total_answered,
        'correct_answers': correct_answers,
        'accuracy_percentage': accuracy,
        'total_points_earned': total_points_from_quiz,
        'current_points_balance': request.user.points_balance
    })
