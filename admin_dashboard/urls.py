# admin_dashboard/urls.py
from django.urls import path
from . import views

app_name = 'admin_dashboard'

urlpatterns = [
    # Dashboard & Analytics
    path('', views.admin_dashboard, name='dashboard'),
    path('analytics/', views.platform_analytics, name='analytics'),
    path('export/', views.export_data, name='export_data'),

    # User Management
    path('users/', views.UserManagementView.as_view(), name='user_management'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/<int:user_id>/delete/', views.delete_user_profile, name='delete_user'),

    # Quiz Management
    path('quiz/', views.quiz_management, name='quiz_management'),
    path('quiz/create/', views.create_question, name='create_question'),
    path('quiz/generate/', views.generate_questions, name='generate_questions'),
    path('quiz/<int:question_id>/', views.question_detail, name='question_detail'),
    path('quiz/<int:question_id>/delete/', views.delete_question, name='delete_question'),
    path('quiz/<int:question_id>/toggle/', views.toggle_question_status, name='toggle_question_status'),
    path('quiz/<int:question_id>/set-daily/', views.set_daily_quiz, name='set_daily_quiz'),

    # Payment Packages Management
    path('packages/', views.packages_management, name='packages_management'),
    path('packages/create/', views.create_package, name='create_package'),
    path('packages/<int:package_id>/edit/', views.edit_package, name='edit_package'),
    path('packages/<int:package_id>/delete/', views.delete_package, name='delete_package'),

    # Purchases Management
    path('purchases/', views.purchases_management, name='purchases_management'),
    path('purchases/<int:purchase_id>/', views.purchase_detail, name='purchase_detail'),

    # Rewards Management
    path('rewards/', views.rewards_management, name='rewards_management'),
    path('rewards/create/', views.create_reward, name='create_reward'),
    path('rewards/<int:reward_id>/edit/', views.edit_reward, name='edit_reward'),
    path('rewards/<int:reward_id>/delete/', views.delete_reward, name='delete_reward'),
    path('rewards/<int:reward_id>/toggle/', views.toggle_reward_status, name='toggle_reward_status'),

    # Reward Claims Management
    path('reward-claims/', views.reward_claims_management, name='reward_claims'),
    path('reward-claims/<int:claim_id>/update/', views.update_reward_claim_status, name='update_reward_claim_status'),

    # Advertisements Management
    path('advertisements/', views.advertisements_management, name='advertisements_management'),
    path('advertisements/create/', views.create_advertisement, name='create_advertisement'),
    path('advertisements/<int:ad_id>/edit/', views.edit_advertisement, name='edit_advertisement'),
    path('advertisements/<int:ad_id>/delete/', views.delete_advertisement, name='delete_advertisement'),
    path('advertisements/<int:ad_id>/toggle/', views.toggle_advertisement_status, name='toggle_advertisement_status'),

    # Referrals Management
    path('referrals/', views.referrals_management, name='referrals_management'),

    # Profile Management
    path('profile/<int:user_id>/edit/', views.edit_profile, name='edit_profile'),
]
