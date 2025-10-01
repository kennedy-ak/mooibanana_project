from django.urls import path
from . import views

app_name = 'quiz'

urlpatterns = [
    path('daily/', views.get_daily_quiz, name='daily_quiz'),
    path('submit/', views.submit_quiz_answer, name='submit_answer'),
    path('stats/', views.quiz_stats, name='stats'),
]