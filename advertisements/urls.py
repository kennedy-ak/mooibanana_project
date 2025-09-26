from django.urls import path
from . import views

app_name = 'advertisements'

urlpatterns = [
    path('api/active/', views.get_active_advertisements, name='active_ads'),
]