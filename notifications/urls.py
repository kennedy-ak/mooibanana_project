# notifications/urls.py
from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.NotificationListView.as_view(), name='list'),
    path('send-match-request/<int:user_id>/', views.send_match_request, name='send_match_request'),
    path('respond/<int:notification_id>/', views.respond_to_match_request, name='respond_to_match_request'),
    path('api/get/', views.get_notifications, name='get_notifications'),
    path('api/mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_read'),
]
