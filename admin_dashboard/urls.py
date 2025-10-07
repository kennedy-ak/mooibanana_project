# admin_dashboard/urls.py
from django.urls import path
from . import views

app_name = 'admin_dashboard'

urlpatterns = [
    path('', views.admin_dashboard, name='dashboard'),
    path('users/', views.UserManagementView.as_view(), name='user_management'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/<int:user_id>/delete/', views.delete_user_profile, name='delete_user'),
    path('analytics/', views.platform_analytics, name='analytics'),
    path('export/', views.export_data, name='export_data'),
    path('quiz/', views.quiz_management, name='quiz_management'),
    path('quiz/create/', views.create_question, name='create_question'),
    path('quiz/generate/', views.generate_questions, name='generate_questions'),
    path('quiz/<int:question_id>/', views.question_detail, name='question_detail'),
    path('quiz/<int:question_id>/delete/', views.delete_question, name='delete_question'),
    path('quiz/<int:question_id>/toggle/', views.toggle_question_status, name='toggle_question_status'),
    path('quiz/<int:question_id>/set-daily/', views.set_daily_quiz, name='set_daily_quiz'),
]
