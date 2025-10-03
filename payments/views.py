# payments/views.py
import requests
import json
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import LikePackage, DislikePackage, Purchase
import hashlib
import hmac

User = get_user_model()

# Import notification model and utils
try:
    from notifications.models import Notification
    from notifications.utils import broadcast_notification
except ImportError:
    Notification = None
    broadcast_notification = None

class PricingView(ListView):
    """Public pricing page - no login required"""
    model = LikePackage
    template_name = 'payments/pricing.html'
    context_object_name = 'packages'
    
    def get_queryset(self):
        return LikePackage.objects.filter(is_active=True).order_by('price')

class PackagesView(LoginRequiredMixin, TemplateView):
    template_name = 'payments/packages.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        package_type = self.request.GET.get('type', 'likes')
        
        if package_type == 'likes':
            context['packages'] = LikePackage.objects.filter(is_active=True).order_by('price')
            context['package_type'] = 'likes'
            context['page_title'] = 'Like Packages'
        elif package_type == 'dislikes':
            context['packages'] = DislikePackage.objects.filter(is_active=True).order_by('price')
            context['package_type'] = 'dislikes'
            context['page_title'] = 'Dislike Packages'
        else:
            # Default to likes
            context['packages'] = LikePackage.objects.filter(is_active=True).order_by('price')
            context['package_type'] = 'likes'
            context['page_title'] = 'Like Packages'
        
        return context

@login_required
def packages_api(request):
    """API endpoint to return packages as JSON"""
    package_type = request.GET.get('type', 'likes')
    
    if package_type == 'dislikes':
        packages = DislikePackage.objects.filter(is_active=True)
        data = {
            'packages': [{
                'id': package.id,
                'name': package.name,
                'price': float(package.price),
                'regular_likes': 0,
                'super_likes': 0,
                'unlikes': package.unlikes,
                'boosters': 0,
                'description': package.description,
                'package_type': 'dislike'
            } for package in packages]
        }
    else:
        packages = LikePackage.objects.filter(is_active=True)
        data = {
            'packages': [{
                'id': package.id,
                'name': package.name,
                'price': float(package.price),
                'regular_likes': package.regular_likes,
                'super_likes': package.super_likes,
                'unlikes': 0,
                'boosters': package.boosters,
                'description': package.description,
                'package_type': 'like'
            } for package in packages]
        }
    
    return JsonResponse(data)

@login_required
def purchase_like_package(request, package_id):
    package = get_object_or_404(LikePackage, id=package_id, is_active=True)
    
    # Check if user has email
    if not request.user.email:
        messages.error(request, 'Je moet een geldig e-mailadres hebben om te kunnen betalen.')
        return redirect('payments:packages')
    
    try:
        # Create purchase record
        purchase = Purchase.objects.create(
            user=request.user,
            package_type='like',
            like_package=package,
            amount=package.price,
            status='pending'
        )
        
        # Initialize Paystack transaction
        paystack_data = {
            'email': request.user.email,
            'amount': int(package.price * 100),  # Convert to pesewas (GHS uses pesewas like kobo)
            'currency': 'GHS',  # Ghana Cedis
            'reference': f'purchase_{purchase.id}_{request.user.id}',
            'callback_url': request.build_absolute_uri(reverse('payments:paystack_callback')),
            'metadata': {
                'user_id': str(request.user.id),
                'package_id': str(package.id),
                'purchase_id': str(purchase.id),
                'purchase_type': 'self',
                'package_type': 'like',
            }
        }
        
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json',
        }
        
        print(f"Paystack data: {paystack_data}")  # Debug print
        print(f"Headers: {headers}")  # Debug print
        
        response = requests.post(
            'https://api.paystack.co/transaction/initialize',
            headers=headers,
            data=json.dumps(paystack_data)
        )
        
        print(f"Response status: {response.status_code}")  # Debug print
        print(f"Response content: {response.text}")  # Debug print
        
        if response.status_code == 200:
            paystack_response = response.json()
            if paystack_response['status']:
                # Store the reference for verification
                purchase.paystack_reference = paystack_data['reference']
                purchase.save()
                
                # Redirect to Paystack payment page
                return redirect(paystack_response['data']['authorization_url'])
            else:
                error_msg = paystack_response.get('message', 'Payment initialization failed')
                messages.error(request, f'Payment failed: {error_msg}')
                purchase.delete()
                return redirect('payments:packages')
        else:
            messages.error(request, f'Payment service error: {response.status_code}')
            purchase.delete()
            return redirect('payments:packages')
        
    except Exception as e:
        messages.error(request, f'Payment error: {str(e)}')
        print(f"Exception: {e}")  # Debug print
        return redirect('payments:packages')

@login_required
def purchase_dislike_package(request, package_id):
    package = get_object_or_404(DislikePackage, id=package_id, is_active=True)
    
    # Check if user has email
    if not request.user.email:
        messages.error(request, 'Je moet een geldig e-mailadres hebben om te kunnen betalen.')
        return redirect('payments:packages')
    
    try:
        # Create purchase record
        purchase = Purchase.objects.create(
            user=request.user,
            package_type='dislike',
            dislike_package=package,
            amount=package.price,
            status='pending'
        )
        
        # Initialize Paystack transaction
        paystack_data = {
            'email': request.user.email,
            'amount': int(package.price * 100),  # Convert to pesewas (GHS uses pesewas like kobo)
            'currency': 'GHS',  # Ghana Cedis
            'reference': f'dislike_purchase_{purchase.id}_{request.user.id}',
            'callback_url': request.build_absolute_uri(reverse('payments:paystack_callback')),
            'metadata': {
                'user_id': str(request.user.id),
                'package_id': str(package.id),
                'purchase_id': str(purchase.id),
                'purchase_type': 'self',
                'package_type': 'dislike',
            }
        }
        
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json',
        }
        
        print(f"Paystack data: {paystack_data}")  # Debug print
        print(f"Headers: {headers}")  # Debug print
        
        response = requests.post(
            'https://api.paystack.co/transaction/initialize',
            headers=headers,
            data=json.dumps(paystack_data)
        )
        
        print(f"Response status: {response.status_code}")  # Debug print
        print(f"Response content: {response.text}")  # Debug print
        
        if response.status_code == 200:
            paystack_response = response.json()
            if paystack_response['status']:
                # Store the reference for verification
                purchase.paystack_reference = paystack_data['reference']
                purchase.save()
                
                # Redirect to Paystack payment page
                return redirect(paystack_response['data']['authorization_url'])
            else:
                error_msg = paystack_response.get('message', 'Payment initialization failed')
                messages.error(request, f'Payment failed: {error_msg}')
                purchase.delete()
                return redirect('payments:packages')
        else:
            messages.error(request, f'Payment service error: {response.status_code}')
            purchase.delete()
            return redirect('payments:packages')
        
    except Exception as e:
        messages.error(request, f'Payment error: {str(e)}')
        print(f"Exception: {e}")  # Debug print
        return redirect('payments:packages')

@login_required
def gift_package(request, package_id, recipient_id):
    """Handle gift purchase for another user"""
    package = get_object_or_404(LikePackage, id=package_id, is_active=True)
    recipient = get_object_or_404(User, id=recipient_id)
    
    # Prevent self-gifting
    if request.user == recipient:
        messages.error(request, 'Je kunt geen likes voor jezelf kopen!')
        return redirect('profiles:profile_detail', pk=recipient_id)
    
    try:
        # Create purchase record
        purchase = Purchase.objects.create(
            user=request.user,  # The person paying
            package=package,
            amount=package.price,
            status='pending'
        )
        
        # Initialize Paystack transaction for gift
        paystack_data = {
            'email': request.user.email,
            'amount': int(package.price * 100),  # Convert to pesewas
            'currency': 'GHS',  # Ghana Cedis
            'reference': f'gift_{purchase.id}_{request.user.id}_{recipient.id}',
            'callback_url': request.build_absolute_uri(reverse('payments:paystack_callback')),
            'metadata': {
                'user_id': str(request.user.id),
                'package_id': str(package.id),
                'purchase_id': str(purchase.id),
                'recipient_id': str(recipient.id),
                'purchase_type': 'gift',
                'recipient_name': recipient.first_name or recipient.username,
            }
        }
        
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json',
        }
        
        response = requests.post(
            'https://api.paystack.co/transaction/initialize',
            headers=headers,
            data=json.dumps(paystack_data)
        )
        
        if response.status_code == 200:
            paystack_response = response.json()
            if paystack_response['status']:
                # Store the reference for verification
                purchase.paystack_reference = paystack_data['reference']
                purchase.save()
                
                # Redirect to Paystack payment page
                return redirect(paystack_response['data']['authorization_url'])
            else:
                messages.error(request, 'Payment initialization failed')
                purchase.delete()
                return redirect('profiles:profile_detail', pk=recipient_id)
        else:
            messages.error(request, 'Payment service unavailable')
            purchase.delete()
            return redirect('profiles:profile_detail', pk=recipient_id)
        
    except Exception as e:
        messages.error(request, f'Payment error: {str(e)}')
        return redirect('profiles:profile_detail', pk=recipient_id)

@login_required
def paystack_callback(request):
    """Handle Paystack payment callback"""
    reference = request.GET.get('reference')
    
    if not reference:
        messages.error(request, 'Invalid payment reference')
        return redirect('payments:packages')
    
    try:
        # Verify payment with Paystack
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json',
        }
        
        response = requests.get(
            f'https://api.paystack.co/transaction/verify/{reference}',
            headers=headers
        )
        
        if response.status_code == 200:
            paystack_data = response.json()
            
            if paystack_data['status'] and paystack_data['data']['status'] == 'success':
                # Payment successful
                try:
                    purchase = Purchase.objects.get(paystack_reference=reference)
                    
                    if purchase.status != 'completed':
                        purchase.status = 'completed'
                        purchase.completed_at = timezone.now()
                        purchase.save()
                        
                        # Process the purchase based on package type and purchase type
                        metadata = paystack_data['data']['metadata']
                        purchase_type = metadata.get('purchase_type', 'self')
                        package_type = metadata.get('package_type', 'like')
                        
                        print(f"DEBUG: Processing payment - purchase_type: {purchase_type}, package_type: {package_type}, metadata: {metadata}")  # Debug line
                        
                        if purchase_type == 'gift' and 'recipient_id' in metadata:
                            # Gift purchase - handle based on package type
                            try:
                                recipient = User.objects.get(id=metadata['recipient_id'])
                                package = purchase.package
                                
                                if package_type == 'like':
                                    # Give regular likes to recipient
                                    recipient.likes_balance += package.regular_likes
                                    # Give super likes and boosters to purchaser
                                    if package.super_likes > 0:
                                        purchase.user.super_likes_balance += package.super_likes
                                    # Save both users
                                    recipient.save()
                                    purchase.user.save()
                                    
                                    # Create notification
                                    if Notification:
                                        notification = Notification.objects.create(
                                            sender=purchase.user,
                                            receiver=recipient,
                                            notification_type='gift_received',
                                            message=f'You received a gift: {package.regular_likes} regular likes from {purchase.user.first_name or purchase.user.username}!'
                                        )
                                        if broadcast_notification:
                                            broadcast_notification(notification)
                                    
                                    recipient_name = metadata.get("recipient_name", "unknown")
                                    messages.success(request, f'Gift sent successfully! {package.regular_likes} regular likes to {recipient_name}!')
                                    
                                elif package_type == 'dislike':
                                    # Give unlikes to recipient
                                    recipient.unlikes_balance += package.unlikes
                                    recipient.save()
                                    
                                    # Create notification
                                    if Notification:
                                        notification = Notification.objects.create(
                                            sender=purchase.user,
                                            receiver=recipient,
                                            notification_type='gift_received',
                                            message=f'You received a gift: {package.unlikes} dislikes from {purchase.user.first_name or purchase.user.username}!'
                                        )
                                        if broadcast_notification:
                                            broadcast_notification(notification)
                                    
                                    recipient_name = metadata.get("recipient_name", "unknown")
                                    messages.success(request, f'Gift sent successfully! {package.unlikes} dislikes to {recipient_name}!')
                                
                                # Redirect back to the recipient's profile for gift purchases
                                return redirect('profiles:profile_detail', pk=recipient.id)
                            except User.DoesNotExist:
                                messages.error(request, 'Recipient not found')
                                return redirect('payments:success')
                        else:
                            # Regular purchase - add to buyer based on package type
                            package = purchase.package
                            
                            if package_type == 'like':
                                purchase.user.likes_balance += package.regular_likes
                                if package.super_likes > 0:
                                    purchase.user.super_likes_balance += package.super_likes
                                purchase.user.save()
                                
                                # Create success message
                                success_parts = [f'{package.regular_likes} likes']
                                if package.super_likes > 0:
                                    success_parts.append(f'{package.super_likes} super likes')
                                messages.success(request, f'Payment successful! You received {", ".join(success_parts)}.')
                                
                            elif package_type == 'dislike':
                                purchase.user.unlikes_balance += package.unlikes
                                purchase.user.save()
                                
                                messages.success(request, f'Payment successful! You received {package.unlikes} dislikes.')
                            
                            # Redirect to success page for regular purchases
                            return redirect('payments:success')
                except Purchase.DoesNotExist:
                    messages.error(request, 'Purchase not found')
                    return redirect('payments:packages')
            else:
                messages.error(request, 'Payment verification failed')
                return redirect('payments:cancel')
        else:
            messages.error(request, 'Payment verification failed')
            return redirect('payments:cancel')
            
    except Exception as e:
        messages.error(request, f'Payment verification error: {str(e)}')
        return redirect('payments:cancel')

class PaymentSuccessView(LoginRequiredMixin, TemplateView):
    template_name = 'payments/success.html'

class PaymentCancelView(LoginRequiredMixin, TemplateView):
    template_name = 'payments/cancel.html'

@csrf_exempt
def paystack_webhook(request):
    """Handle Paystack webhook notifications"""
    # Verify webhook signature
    signature = request.META.get('HTTP_X_PAYSTACK_SIGNATURE')
    payload = request.body
    
    if not signature:
        return HttpResponse(status=400)
    
    # Compute expected signature
    expected_signature = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode('utf-8'),
        payload,
        hashlib.sha512
    ).hexdigest()
    
    if not hmac.compare_digest(signature, expected_signature):
        return HttpResponse(status=400)
    
    try:
        event = json.loads(payload.decode('utf-8'))
        
        if event['event'] == 'charge.success':
            data = event['data']
            reference = data['reference']
            
            try:
                purchase = Purchase.objects.get(paystack_reference=reference)
                
                if purchase.status != 'completed':
                    purchase.status = 'completed'
                    purchase.completed_at = timezone.now()
                    purchase.save()
                    
                    # Process likes based on metadata
                    metadata = data.get('metadata', {})
                    purchase_type = metadata.get('purchase_type', 'self')
                    
                    if purchase_type == 'gift' and 'recipient_id' in metadata:
                        # Gift purchase - regular likes to recipient, super likes and boosters to purchaser
                        try:
                            recipient = User.objects.get(id=metadata['recipient_id'])

                            # Give regular likes to recipient
                            recipient.likes_balance += purchase.package.regular_likes
                            recipient.save()

                            # Give super likes and boosters to purchaser
                            if purchase.package.super_likes > 0:
                                purchase.user.super_likes_balance = getattr(purchase.user, 'super_likes_balance', 0) + purchase.package.super_likes
                            
                            if purchase.package.boosters > 0:
                                # Add boosters to purchaser (implement boosters later if needed)
                                pass
                            
                            purchase.user.save()

                            # Create notification for recipient about the gift
                            if Notification:
                                Notification.objects.create(
                                    sender=purchase.user,
                                    receiver=recipient,
                                    notification_type='gift_received',
                                    message=f'You received a gift: {purchase.package.regular_likes} regular likes from {purchase.user.first_name or purchase.user.username}!'
                                )
                        except User.DoesNotExist:
                            pass
                    else:
                        # Regular purchase
                        purchase.user.likes_balance += purchase.package.regular_likes
                        if purchase.package.super_likes > 0:
                            purchase.user.super_likes_balance = getattr(purchase.user, 'super_likes_balance', 0) + purchase.package.super_likes
                        purchase.user.save()
                        
            except Purchase.DoesNotExist:
                pass
                
    except (json.JSONDecodeError, KeyError):
        return HttpResponse(status=400)
    
    return HttpResponse(status=200)