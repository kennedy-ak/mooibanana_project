
# chat/admin.py
from django.contrib import admin
from .models import ChatRoom, Message, Match

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ['id', 'created_at']
    filter_horizontal = ['participants']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'room', 'content', 'timestamp', 'is_read']
    list_filter = ['is_read', 'timestamp']
    search_fields = ['sender__username', 'content']

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ['user1', 'user2', 'created_at']
    search_fields = ['user1__username', 'user2__username']