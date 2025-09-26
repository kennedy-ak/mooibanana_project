from django.urls import path
from . import views

app_name = 'updates'

urlpatterns = [
    path('feed/', views.UpdatesFeedView.as_view(), name='feed'),
    path('post/', views.PostUpdateView.as_view(), name='post'),
    path('post-form/', views.post_update_form, name='post_form'),
    path('my-updates/', views.MyUpdatesView.as_view(), name='my_updates'),
    path('delete/<int:update_id>/', views.delete_update, name='delete'),
]