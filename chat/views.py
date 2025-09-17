# chat/views.py
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.http import JsonResponse
from django.db.models import Q
from .models import ChatRoom, Message, Match

class ChatListView(LoginRequiredMixin, ListView):
    template_name = 'chat/list.html'
    context_object_name = 'chat_rooms'

    def get_queryset(self):
        return ChatRoom.objects.filter(
            participants=self.request.user
        ).prefetch_related('participants', 'messages')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add other user information for each chat room
        chat_rooms_with_other_user = []
        for room in context['chat_rooms']:
            other_user = room.participants.exclude(id=self.request.user.id).first()
            chat_rooms_with_other_user.append({
                'room': room,
                'other_user': other_user
            })
        context['chat_rooms_with_other_user'] = chat_rooms_with_other_user
        return context

class ChatRoomView(LoginRequiredMixin, DetailView):
    model = ChatRoom
    template_name = 'chat/room.html'
    context_object_name = 'room'
    pk_url_kwarg = 'room_id'

    def get_queryset(self):
        return ChatRoom.objects.filter(participants=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Mark messages as read
        self.object.messages.filter(is_read=False).exclude(sender=self.request.user).update(is_read=True)
        # Add other user information
        context['other_user'] = self.object.participants.exclude(id=self.request.user.id).first()
        return context

@login_required
def send_message(request):
    if request.method == 'POST':
        room_id = request.POST.get('room_id')
        content = request.POST.get('content')
        
        room = get_object_or_404(ChatRoom, id=room_id, participants=request.user)
        
        if content.strip():
            message = Message.objects.create(
                room=room,
                sender=request.user,
                content=content.strip()
            )
            
            return JsonResponse({
                'success': True,
                'message': {
                    'content': message.content,
                    'sender': message.sender.username,
                    'timestamp': message.timestamp.strftime('%H:%M')
                }
            })
    
    return JsonResponse({'success': False})
