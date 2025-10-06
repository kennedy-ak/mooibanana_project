
# payments/urls.py
from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('pricing/', views.PricingView.as_view(), name='pricing'),
    path('packages/', views.PackagesView.as_view(), name='packages'),
    path('api/packages/', views.packages_api, name='packages_api'),
    path('purchase/like/<int:package_id>/', views.purchase_like_package, name='purchase_like'),
    path('purchase/dislike/<int:package_id>/', views.purchase_dislike_package, name='purchase_dislike'),
    path('gift/<int:package_id>/<int:recipient_id>/', views.gift_package, name='gift_package'),
    path('callback/', views.paystack_callback, name='paystack_callback'),
    path('stripe/success/', views.stripe_success, name='stripe_success'),
    path('success/', views.PaymentSuccessView.as_view(), name='success'),
    path('cancel/', views.PaymentCancelView.as_view(), name='cancel'),
    path('webhook/', views.paystack_webhook, name='paystack_webhook'),
]
