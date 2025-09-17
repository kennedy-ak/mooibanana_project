
# likes/urls.py
from django.urls import path
from . import views

app_name = 'likes'

urlpatterns = [
    path('give/<int:user_id>/', views.give_like, name='give_like'),
    path('my-likes/', views.MyLikesView.as_view(), name='my_likes'),
    path('matches/', views.MatchesView.as_view(), name='matches'),
]
