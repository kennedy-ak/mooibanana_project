
# profiles/urls.py
from django.urls import path
from . import views

app_name = 'profiles'

urlpatterns = [
    path('create/', views.CreateProfileView.as_view(), name='create_profile'),
    path('edit/', views.EditProfileView.as_view(), name='edit_profile'),
    path('discover/', views.DiscoverView.as_view(), name='discover'),
    path('search/', views.DiscoverView.as_view(), name='search'),  # Alias for search
    path('profile/<int:pk>/', views.ProfileDetailView.as_view(), name='profile_detail'),
    path('my-profile/', views.MyProfileView.as_view(), name='my_profile'),
]
