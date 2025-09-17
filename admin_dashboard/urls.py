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
]
