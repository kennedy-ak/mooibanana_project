# social/urls.py
from django.urls import path
from . import views

app_name = 'social'

urlpatterns = [
    # Feed and post URLs
    path('feed/', views.FeedView.as_view(), name='feed'),
    path('post/create/', views.CreatePostView.as_view(), name='create_post'),
    path('post/<int:pk>/', views.PostDetailView.as_view(), name='post_detail'),
    path('post/<int:post_id>/delete/', views.delete_post, name='delete_post'),

    # Follow/Unfollow URLs
    path('follow/<int:user_id>/', views.follow_user, name='follow_user'),
    path('unfollow/<int:user_id>/', views.unfollow_user, name='unfollow_user'),
    path('user/<int:user_id>/followers/', views.FollowersListView.as_view(), name='followers_list'),
    path('user/<int:user_id>/following/', views.FollowingListView.as_view(), name='following_list'),

    # Comment URLs
    path('post/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),

    # Like URLs
    path('post/<int:post_id>/like/', views.like_post, name='like_post'),
    path('comment/<int:comment_id>/like/', views.like_comment, name='like_comment'),
]
