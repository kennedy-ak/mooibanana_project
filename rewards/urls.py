# rewards/urls.py
from django.urls import path
from . import views

app_name = 'rewards'

urlpatterns = [
    path('', views.RewardsListView.as_view(), name='list'),
    path('claim/<int:reward_id>/', views.claim_reward, name='claim'),
    path('my-claims/', views.MyClaimsView.as_view(), name='my_claims'),
]
