# chat/urls.py
from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.ChatListView.as_view(), name='list'),
    path('room/<int:room_id>/', views.ChatRoomView.as_view(), name='room'),
    path('send-message/', views.send_message, name='send_message'),
]