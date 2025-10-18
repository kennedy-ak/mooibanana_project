# payments/views.py
import requests
import json
import stripe
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
from .models import Package, Purchase
import hashlib
import hmac

User = get_user_model()

# Initialize Stripe
stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')

# Import notification model and utils
try:
    from notifications.models import Notification
    from notifications.utils import broadcast_notification
except ImportError:
    Notification = None
    broadcast_notification = None

class PricingView(ListView):
    """Public pricing page - no login required"""
    model = Package
    template_name = 'payments/pricing.html'
    context_object_name = 'packages'

    def get_queryset(self):
        # Show both EUR and GHS packages on public page, or filter if user is logged in
        if self.request.user.is_authenticated and self.request.user.country:
            currency = 'GHS' if self.request.user.country == 'GH' else 'EUR'
            return Package.objects.filter(is_active=True, currency=currency).order_by('price')
        # Default to EUR packages for anonymous users
        return Package.objects.filter(is_active=True, currency='EUR').order_by('price')

class PackagesView(LoginRequiredMixin, TemplateView):
    template_name = 'payments/packages.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Filter packages based on user's country
        currency = 'GHS' if self.request.user.country == 'GH' else 'EUR'
        context['packages'] = Package.objects.filter(is_active=True, currency=currency).order_by('price')
        context['page_title'] = 'Packages'
        context['currency'] = currency
        return context

@login_required
def packages_api(request):
    """API endpoint to return packages as JSON"""
    # Filter packages based on user's country
    currency = 'GHS' if request.user.country == 'GH' else 'EUR'
    packages = Package.objects.filter(is_active=True, currency=currency)
    data = {
        'packages': [{
            'id': package.id,
            'name': package.name,
            'price': float(package.price),
            'currency': package.currency,
            'likes_count': package.likes_count,
            'boosters': package.boosters,
            'points_reward': package.points_reward,
            'description': package.description,
        } for package in packages]
    }

    return JsonResponse(data)

def get_payment_provider(user):
    """Determine which payment provider to use based on user's country"""
    if not user.country:
        return 'paystack'  # Default to Paystack if no country set

    # Ghana uses Paystack
    if user.country == 'GH':
        return 'paystack'

    # European countries use Viva Wallet
    european_countries = ['AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR',
                         'DE', 'GR', 'HU', 'IE', 'IT', 'LV', 'LT', 'LU', 'MT', 'NL',
                         'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE']
    if user.country in european_countries:
        return 'viva'

    return 'paystack'  # Default

@login_required
def purchase_package(request, package_id):
    """Unified package purchase - user chooses usage type (likes or dislikes) at purchase"""
    package = get_object_or_404(Package, id=package_id, is_active=True)
    usage_type = request.GET.get('usage_type', 'likes')  # Default to likes

    # Validate usage_type
    if usage_type not in ['likes', 'dislikes']:
        usage_type = 'likes'

    # Check if user has email
    if not request.user.email:
        messages.error(request, 'Je moet een geldig e-mailadres hebben om te kunnen betalen.')
        return redirect('payments:packages')

    # Check if user has country set
    if not request.user.country:
        messages.error(request, 'Please select your country in your profile settings first.')
        return redirect('payments:packages')

    # Determine payment provider
    payment_provider = get_payment_provider(request.user)

    if payment_provider == 'viva':
        return purchase_package_viva(request, package, usage_type)
    elif payment_provider == 'stripe':
        return purchase_package_stripe(request, package, usage_type)
    else:
        return purchase_package_paystack(request, package, usage_type)

@login_required
def purchase_package_paystack(request, package, usage_type='likes'):
    """Handle Paystack payment for packages"""
    try:
        # Create purchase record
        purchase = Purchase.objects.create(
            user=request.user,
            package=package,
            amount=package.price,
            payment_provider='paystack',
            status='pending',
            usage_type=usage_type
        )

        # Initialize Paystack transaction
        paystack_data = {
            'email': request.user.email,
            'amount': int(package.price * 100),  # Convert to pesewas
            'currency': package.currency,  # Use package currency (should be GHS for Paystack)
            'reference': f'purchase_{purchase.id}_{request.user.id}',
            'callback_url': request.build_absolute_uri(reverse('payments:paystack_callback')),
            'metadata': {
                'user_id': str(request.user.id),
                'package_id': str(package.id),
                'purchase_id': str(purchase.id),
                'purchase_type': 'self',
                'usage_type': usage_type,
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
def purchase_package_stripe(request, package, usage_type='likes'):
    """Handle Stripe payment for packages"""
    try:
        # Create purchase record
        purchase = Purchase.objects.create(
            user=request.user,
            package=package,
            amount=package.price,
            payment_provider='stripe',
            status='pending',
            usage_type=usage_type
        )

        # Create Stripe Checkout Session
        checkout_session = stripe.checkout.Session.create(
            customer_email=request.user.email,
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': package.currency.lower(),  # Use package currency (should be EUR for Stripe)
                    'unit_amount': int(package.price * 100),  # Convert to cents
                    'product_data': {
                        'name': package.name,
                        'description': f'{package.likes_count} likes (for {usage_type})' +
                                     (f', {package.boosters} boosters' if package.boosters > 0 else ''),
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.build_absolute_uri(reverse('payments:stripe_success')) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.build_absolute_uri(reverse('payments:cancel')),
            metadata={
                'user_id': str(request.user.id),
                'package_id': str(package.id),
                'purchase_id': str(purchase.id),
                'purchase_type': 'self',
                'usage_type': usage_type,
            }
        )

        # Store session ID
        purchase.stripe_session_id = checkout_session.id
        purchase.save()

        # Redirect to Stripe Checkout
        return redirect(checkout_session.url)

    except Exception as e:
        messages.error(request, f'Payment error: {str(e)}')
        print(f"Stripe Exception: {e}")  # Debug print
        return redirect('payments:packages')

@login_required
def purchase_package_viva(request, package, usage_type='likes'):
    """Handle Viva Wallet payment for packages"""
    try:
        # Create purchase record
        purchase = Purchase.objects.create(
            user=request.user,
            package=package,
            amount=package.price,
            payment_provider='viva',
            status='pending',
            usage_type=usage_type
        )

        # Get Viva Wallet API base URL based on environment
        api_base = 'https://api.vivapayments.com' if settings.VIVA_ENVIRONMENT == 'production' else 'https://demo-api.vivapayments.com'

        # Prepare order data for Viva Wallet
        order_data = {
            'amount': int(package.price * 100),  # Convert to cents
            'customerTrns': f'{package.name} - {usage_type}',
            'customer': {
                'email': request.user.email,
                'fullName': f'{request.user.first_name} {request.user.last_name}' if request.user.first_name else request.user.username,
            },
            'paymentTimeout': 1800,  # 30 minutes
            'preauth': False,
            'allowRecurring': False,
            'maxInstallments': 0,
            'paymentNotification': True,
            'tipAmount': 0,
            'disableExactAmount': False,
            'disableCash': True,
            'disableWallet': False,
            'sourceCode': settings.VIVA_SOURCE_CODE if settings.VIVA_SOURCE_CODE else None,
            'merchantTrns': f'Purchase #{purchase.id}',
            'tags': [
                f'user_id:{request.user.id}',
                f'package_id:{package.id}',
                f'purchase_id:{purchase.id}',
                f'usage_type:{usage_type}',
                'purchase_type:self',
            ]
        }

        # Remove sourceCode if empty
        if not order_data['sourceCode']:
            del order_data['sourceCode']

        # Create payment order with Viva Wallet API
        headers = {
            'Authorization': f'Bearer {settings.VIVA_API_KEY}',
            'Content-Type': 'application/json',
        }

        response = requests.post(
            f'{api_base}/checkout/v2/orders',
            json=order_data,
            headers=headers,
            auth=(settings.VIVA_MERCHANT_ID, settings.VIVA_API_KEY)
        )

        if response.status_code == 200:
            viva_response = response.json()
            order_code = viva_response.get('orderCode')

            if order_code:
                # Store order code in purchase
                purchase.viva_order_code = order_code
                purchase.save()

                # Construct checkout URL
                checkout_url = f'https://www.vivapayments.com/web/checkout?ref={order_code}' if settings.VIVA_ENVIRONMENT == 'production' else f'https://demo.vivapayments.com/web/checkout?ref={order_code}'

                # Redirect to Viva Wallet checkout page
                return redirect(checkout_url)
            else:
                messages.error(request, 'Payment initialization failed')
                purchase.delete()
                return redirect('payments:packages')
        else:
            error_msg = response.json().get('message', 'Payment initialization failed')
            messages.error(request, f'Payment failed: {error_msg}')
            purchase.delete()
            return redirect('payments:packages')

    except Exception as e:
        messages.error(request, f'Payment error: {str(e)}')
        print(f"Viva Wallet Exception: {e}")  # Debug print
        return redirect('payments:packages')

# Deleted functions: purchase_dislike_package, purchase_dislike_package_paystack, purchase_dislike_package_stripe
# These are no longer needed as we now have a unified package system

@login_required
def gift_package(request, package_id, recipient_id):
    """Handle gift purchase for another user"""
    package = get_object_or_404(Package, id=package_id, is_active=True)
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
            status='pending',
            usage_type='likes'  # Gifts are always for likes
        )

        # Initialize Paystack transaction for gift
        paystack_data = {
            'email': request.user.email,
            'amount': int(package.price * 100),  # Convert to pesewas
            'currency': package.currency,  # Use package currency
            'reference': f'gift_{purchase.id}_{request.user.id}_{recipient.id}',
            'callback_url': request.build_absolute_uri(reverse('payments:paystack_callback')),
            'metadata': {
                'user_id': str(request.user.id),
                'package_id': str(package.id),
                'purchase_id': str(purchase.id),
                'recipient_id': str(recipient.id),
                'purchase_type': 'gift',
                'recipient_name': recipient.first_name or recipient.username,
                'usage_type': 'likes',
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

                        # Process the purchase based on purchase type
                        metadata = paystack_data['data']['metadata']
                        purchase_type = metadata.get('purchase_type', 'self')
                        usage_type = metadata.get('usage_type', 'likes')

                        print(f"DEBUG: Processing payment - purchase_type: {purchase_type}, usage_type: {usage_type}, metadata: {metadata}")  # Debug line

                        if purchase_type == 'gift' and 'recipient_id' in metadata:
                            # Gift purchase - give likes to recipient
                            try:
                                recipient = User.objects.get(id=metadata['recipient_id'])
                                package = purchase.package

                                # Give likes to recipient (all packages now use likes_balance)
                                recipient.likes_balance += package.likes_count
                                recipient.save()

                                # Award points to buyer (not recipient)
                                if package.points_reward > 0:
                                    purchase.user.points_balance += package.points_reward
                                    purchase.user.save()

                                # Create notification
                                if Notification:
                                    notification = Notification.objects.create(
                                        sender=purchase.user,
                                        receiver=recipient,
                                        notification_type='gift_received',
                                        message=f'You received a gift: {package.likes_count} likes from {purchase.user.first_name or purchase.user.username}!'
                                    )
                                    if broadcast_notification:
                                        broadcast_notification(notification)

                                recipient_name = metadata.get("recipient_name", "unknown")
                                messages.success(request, f'Gift sent successfully! {package.likes_count} likes to {recipient_name}!')

                                # Redirect back to the recipient's profile for gift purchases
                                return redirect('profiles:profile_detail', pk=recipient.id)
                            except User.DoesNotExist:
                                messages.error(request, 'Recipient not found')
                                return redirect('payments:success')
                        else:
                            # Regular purchase - add to buyer (all packages now add to likes_balance)
                            package = purchase.package

                            purchase.user.likes_balance += package.likes_count

                            # Award points to buyer
                            if package.points_reward > 0:
                                purchase.user.points_balance += package.points_reward

                            purchase.user.save()

                            # Create success message
                            points_msg = f' and {package.points_reward} points' if package.points_reward > 0 else ''
                            messages.success(request, f'Payment successful! You received {package.likes_count} likes for {usage_type}{points_msg}.')

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

@login_required
def stripe_success(request):
    """Handle Stripe payment success callback"""
    session_id = request.GET.get('session_id')

    if not session_id:
        messages.error(request, 'Invalid payment session')
        return redirect('payments:packages')

    try:
        # Retrieve the Stripe session
        session = stripe.checkout.Session.retrieve(session_id)

        if session.payment_status == 'paid':
            # Find purchase by session ID
            try:
                purchase = Purchase.objects.get(stripe_session_id=session_id)

                if purchase.status != 'completed':
                    purchase.status = 'completed'
                    purchase.completed_at = timezone.now()
                    purchase.save()

                    # Process the purchase based on purchase type
                    metadata = session.metadata
                    purchase_type = metadata.get('purchase_type', 'self')
                    usage_type = metadata.get('usage_type', 'likes')

                    if purchase_type == 'gift' and 'recipient_id' in metadata:
                        # Gift purchase - give likes to recipient
                        try:
                            recipient = User.objects.get(id=metadata['recipient_id'])
                            package = purchase.package

                            # Give likes to recipient (all packages now use likes_balance)
                            recipient.likes_balance += package.likes_count
                            recipient.save()

                            # Award points to buyer (not recipient)
                            if package.points_reward > 0:
                                purchase.user.points_balance += package.points_reward
                                purchase.user.save()

                            if Notification:
                                notification = Notification.objects.create(
                                    sender=purchase.user,
                                    receiver=recipient,
                                    notification_type='gift_received',
                                    message=f'You received a gift: {package.likes_count} likes from {purchase.user.first_name or purchase.user.username}!'
                                )
                                if broadcast_notification:
                                    broadcast_notification(notification)

                            recipient_name = metadata.get("recipient_name", "unknown")
                            messages.success(request, f'Gift sent successfully! {package.likes_count} likes to {recipient_name}!')

                            return redirect('profiles:profile_detail', pk=recipient.id)
                        except User.DoesNotExist:
                            messages.error(request, 'Recipient not found')
                            return redirect('payments:success')
                    else:
                        # Regular purchase - add to buyer (all packages now add to likes_balance)
                        package = purchase.package

                        purchase.user.likes_balance += package.likes_count

                        # Award points to buyer
                        if package.points_reward > 0:
                            purchase.user.points_balance += package.points_reward

                        purchase.user.save()

                        points_msg = f' and {package.points_reward} points' if package.points_reward > 0 else ''
                        messages.success(request, f'Payment successful! You received {package.likes_count} likes for {usage_type}{points_msg}.')

                        return redirect('payments:success')
            except Purchase.DoesNotExist:
                messages.error(request, 'Purchase not found')
                return redirect('payments:packages')
        else:
            messages.error(request, 'Payment not completed')
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
                    usage_type = metadata.get('usage_type', 'likes')

                    if purchase_type == 'gift' and 'recipient_id' in metadata:
                        # Gift purchase - likes to recipient
                        try:
                            recipient = User.objects.get(id=metadata['recipient_id'])

                            # Give likes to recipient (all packages now use likes_balance)
                            recipient.likes_balance += purchase.package.likes_count
                            recipient.save()

                            # Award points to buyer (not recipient)
                            if purchase.package.points_reward > 0:
                                purchase.user.points_balance += purchase.package.points_reward
                                purchase.user.save()

                            # Create notification for recipient about the gift
                            if Notification:
                                Notification.objects.create(
                                    sender=purchase.user,
                                    receiver=recipient,
                                    notification_type='gift_received',
                                    message=f'You received a gift: {purchase.package.likes_count} likes from {purchase.user.first_name or purchase.user.username}!'
                                )
                        except User.DoesNotExist:
                            pass
                    else:
                        # Regular purchase - all packages now add to likes_balance
                        purchase.user.likes_balance += purchase.package.likes_count

                        # Award points to buyer
                        if purchase.package.points_reward > 0:
                            purchase.user.points_balance += purchase.package.points_reward

                        purchase.user.save()

            except Purchase.DoesNotExist:
                pass

    except (json.JSONDecodeError, KeyError):
        return HttpResponse(status=400)

    return HttpResponse(status=200)

# Keep old function names for backward compatibility
purchase_like_package = purchase_package
purchase_like_package_paystack = purchase_package_paystack
purchase_like_package_stripe = purchase_package_stripe