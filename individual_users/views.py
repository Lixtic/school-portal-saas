import json
import logging
import uuid

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from individual_users.forms import (
    APIKeyForm,
    EmailSigninForm,
    EmailSignupForm,
    PhoneSigninForm,
    PhoneSignupForm,
)
from individual_users.models import AddonSubscription, APIKey, IndividualProfile

logger = logging.getLogger(__name__)
User = get_user_model()

# ── Available Addons Catalog ─────────────────────────────────────────────────

ADDON_CATALOG = [
    {
        'slug': 'ai-tutor',
        'name': 'AI Tutor API',
        'icon': 'bi-robot',
        'description': 'Intelligent tutoring with adaptive learning paths, powered by GPT.',
        'plans': ['free', 'pro'],
        'category': 'ai',
    },
    {
        'slug': 'grade-analytics',
        'name': 'Grade Analytics API',
        'icon': 'bi-graph-up-arrow',
        'description': 'Student performance analytics, trend detection, and grade prediction.',
        'plans': ['free', 'pro', 'enterprise'],
        'category': 'analytics',
    },
    {
        'slug': 'attendance-tracker',
        'name': 'Attendance Tracker API',
        'icon': 'bi-calendar-check',
        'description': 'Real-time attendance tracking, absence alerts, and reporting.',
        'plans': ['free', 'pro'],
        'category': 'management',
    },
    {
        'slug': 'lesson-planner',
        'name': 'Lesson Planner API',
        'icon': 'bi-journal-bookmark',
        'description': 'AI-generated lesson plans aligned to GES curriculum standards.',
        'plans': ['pro', 'enterprise'],
        'category': 'ai',
    },
    {
        'slug': 'exam-generator',
        'name': 'Exam Generator API',
        'icon': 'bi-file-earmark-text',
        'description': 'Auto-generate quizzes and exam papers from topics or syllabi.',
        'plans': ['pro', 'enterprise'],
        'category': 'ai',
    },
    {
        'slug': 'fee-manager',
        'name': 'Fee Management API',
        'icon': 'bi-cash-stack',
        'description': 'Fee structure creation, payment tracking, and receipt generation.',
        'plans': ['starter', 'pro'],
        'category': 'finance',
    },
    {
        'slug': 'sms-gateway',
        'name': 'SMS & Notification API',
        'icon': 'bi-chat-dots',
        'description': 'Send SMS alerts, push notifications, and email digests.',
        'plans': ['starter', 'pro', 'enterprise'],
        'category': 'communication',
    },
    {
        'slug': 'report-card',
        'name': 'Report Card API',
        'icon': 'bi-file-earmark-bar-graph',
        'description': 'Generate formatted PDF report cards with grade summaries.',
        'plans': ['pro', 'enterprise'],
        'category': 'documents',
    },
]


def _ensure_public_schema():
    """Ensure we're operating on the public schema for individual user queries."""
    connection.set_schema_to_public()


def _individual_required(view_func):
    """Decorator: require login + user_type='individual'."""
    from functools import wraps

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('individual:signin')
        if request.user.user_type != 'individual':
            messages.error(request, 'Access restricted to individual accounts.')
            return redirect('home')
        _ensure_public_schema()
        return view_func(request, *args, **kwargs)

    return wrapper


# ── Auth Views ───────────────────────────────────────────────────────────────

def signup_view(request):
    """Combined signup page: Email / Phone / Google tabs."""
    if request.user.is_authenticated and request.user.user_type == 'individual':
        return redirect('individual:dashboard')

    _ensure_public_schema()
    email_form = EmailSignupForm()
    phone_form = PhoneSignupForm()
    active_tab = 'email'
    method = request.POST.get('signup_method', '')

    if request.method == 'POST':
        if method == 'email':
            active_tab = 'email'
            email_form = EmailSignupForm(request.POST)
            if email_form.is_valid():
                name_parts = email_form.cleaned_data['full_name'].split(None, 1)
                first = name_parts[0]
                last = name_parts[1] if len(name_parts) > 1 else ''
                email = email_form.cleaned_data['email']
                # Username from email prefix + short random suffix
                base = email.split('@')[0][:20]
                username = f"{base}_{uuid.uuid4().hex[:6]}"

                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=email_form.cleaned_data['password'],
                    first_name=first,
                    last_name=last,
                    user_type='individual',
                )
                IndividualProfile.objects.create(user=user)
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                request.session.pop('auth_tenant_schema', None)
                messages.success(request, f'Welcome, {first}! Your account is ready.')
                return redirect('individual:dashboard')

        elif method == 'phone':
            active_tab = 'phone'
            phone_form = PhoneSignupForm(request.POST)
            if phone_form.is_valid():
                name_parts = phone_form.cleaned_data['full_name'].split(None, 1)
                first = name_parts[0]
                last = name_parts[1] if len(name_parts) > 1 else ''
                phone = phone_form.cleaned_data['phone']
                username = f"phone_{uuid.uuid4().hex[:8]}"

                user = User.objects.create_user(
                    username=username,
                    password=phone_form.cleaned_data['password'],
                    first_name=first,
                    last_name=last,
                    user_type='individual',
                    phone=phone,
                )
                IndividualProfile.objects.create(user=user, phone_number=phone)
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                request.session.pop('auth_tenant_schema', None)
                messages.success(request, f'Welcome, {first}! Your account is ready.')
                return redirect('individual:dashboard')

    ctx = {
        'email_form': email_form,
        'phone_form': phone_form,
        'active_tab': active_tab,
        'google_client_id': getattr(settings, 'GOOGLE_OAUTH_CLIENT_ID', ''),
    }
    return render(request, 'individual/auth.html', ctx)


def signin_view(request):
    """Combined signin page: Email / Phone / Google tabs."""
    if request.user.is_authenticated and request.user.user_type == 'individual':
        return redirect('individual:dashboard')

    _ensure_public_schema()
    email_form = EmailSigninForm()
    phone_form = PhoneSigninForm()
    active_tab = 'email'
    method = request.POST.get('signin_method', '')

    if request.method == 'POST':
        if method == 'email':
            active_tab = 'email'
            email_form = EmailSigninForm(request.POST)
            if email_form.is_valid():
                user = authenticate(
                    request,
                    email=email_form.cleaned_data['email'],
                    password=email_form.cleaned_data['password'],
                )
                if user:
                    login(request, user, backend='individual_users.backends.EmailOrPhoneBackend')
                    request.session.pop('auth_tenant_schema', None)
                    return redirect('individual:dashboard')
                else:
                    messages.error(request, 'Invalid email or password.')

        elif method == 'phone':
            active_tab = 'phone'
            phone_form = PhoneSigninForm(request.POST)
            if phone_form.is_valid():
                user = authenticate(
                    request,
                    phone=phone_form.cleaned_data['phone'],
                    password=phone_form.cleaned_data['password'],
                )
                if user:
                    login(request, user, backend='individual_users.backends.EmailOrPhoneBackend')
                    request.session.pop('auth_tenant_schema', None)
                    return redirect('individual:dashboard')
                else:
                    messages.error(request, 'Invalid phone number or password.')

    ctx = {
        'email_form': email_form,
        'phone_form': phone_form,
        'active_tab': active_tab,
        'google_client_id': getattr(settings, 'GOOGLE_OAUTH_CLIENT_ID', ''),
        'is_signin': True,
    }
    return render(request, 'individual/auth.html', ctx)


@require_POST
def google_auth_view(request):
    """Handle Google Sign-In credential verification."""
    _ensure_public_schema()
    try:
        from google.auth.transport import requests as google_requests
        from google.oauth2 import id_token
    except ImportError:
        return JsonResponse({'error': 'Google auth not configured'}, status=500)

    credential = request.POST.get('credential', '')
    if not credential:
        return JsonResponse({'error': 'Missing credential'}, status=400)

    client_id = getattr(settings, 'GOOGLE_OAUTH_CLIENT_ID', '')
    if not client_id:
        return JsonResponse({'error': 'Google OAuth not configured'}, status=500)

    try:
        idinfo = id_token.verify_oauth2_token(
            credential, google_requests.Request(), client_id,
        )
    except ValueError:
        return JsonResponse({'error': 'Invalid Google token'}, status=400)

    google_id = idinfo['sub']
    email = idinfo.get('email', '')
    name = idinfo.get('name', '')
    picture = idinfo.get('picture', '')

    # Try to find existing user by google_id
    profile = IndividualProfile.objects.filter(google_id=google_id).select_related('user').first()

    if profile:
        user = profile.user
    else:
        # Check if a user with this email already exists
        existing = User.objects.filter(email=email, user_type='individual').first()
        if existing:
            profile, _ = IndividualProfile.objects.get_or_create(user=existing)
            profile.google_id = google_id
            profile.avatar_url = picture
            profile.save()
            user = existing
        else:
            # New user
            name_parts = name.split(None, 1)
            first = name_parts[0] if name_parts else email.split('@')[0]
            last = name_parts[1] if len(name_parts) > 1 else ''
            username = f"g_{uuid.uuid4().hex[:10]}"

            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first,
                last_name=last,
                user_type='individual',
            )
            user.set_unusable_password()
            user.save()
            IndividualProfile.objects.create(
                user=user, google_id=google_id, avatar_url=picture,
            )

    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    request.session.pop('auth_tenant_schema', None)
    return JsonResponse({'ok': True, 'redirect': '/u/dashboard/'})


def signout_view(request):
    logout(request)
    return redirect('individual:signin')


# ── Dashboard ────────────────────────────────────────────────────────────────

@_individual_required
def dashboard_view(request):
    profile, _ = IndividualProfile.objects.get_or_create(user=request.user)
    subscriptions = AddonSubscription.objects.filter(profile=profile, status='active')
    api_keys = APIKey.objects.filter(profile=profile)
    total_calls = sum(k.calls_total for k in api_keys)
    active_keys = api_keys.filter(is_active=True).count()

    ctx = {
        'profile': profile,
        'subscriptions': subscriptions,
        'subscription_count': subscriptions.count(),
        'api_keys': api_keys,
        'api_key_count': active_keys,
        'total_api_calls': total_calls,
        'addon_catalog': ADDON_CATALOG,
        'catalog_count': len(ADDON_CATALOG),
    }
    return render(request, 'individual/dashboard.html', ctx)


# ── Addon Marketplace ────────────────────────────────────────────────────────

@_individual_required
def addons_view(request):
    profile = request.user.individual_profile
    my_slugs = set(
        AddonSubscription.objects.filter(profile=profile, status='active')
        .values_list('addon_slug', flat=True)
    )
    catalog = []
    for addon in ADDON_CATALOG:
        catalog.append({**addon, 'subscribed': addon['slug'] in my_slugs})

    ctx = {
        'catalog': catalog,
        'profile': profile,
        'categories': sorted({a['category'] for a in ADDON_CATALOG}),
    }
    return render(request, 'individual/addons.html', ctx)


@_individual_required
@require_POST
def subscribe_addon(request):
    profile = request.user.individual_profile
    slug = request.POST.get('addon_slug', '')
    plan = request.POST.get('plan', 'free')

    addon = next((a for a in ADDON_CATALOG if a['slug'] == slug), None)
    if not addon:
        return JsonResponse({'error': 'Addon not found'}, status=404)
    if plan not in addon['plans']:
        return JsonResponse({'error': 'Plan not available for this addon'}, status=400)

    sub, created = AddonSubscription.objects.update_or_create(
        profile=profile, addon_slug=slug,
        defaults={
            'addon_name': addon['name'],
            'plan': plan,
            'status': 'active',
            'expires_at': None,
        },
    )
    return JsonResponse({'ok': True, 'created': created, 'addon': addon['name']})


@_individual_required
@require_POST
def unsubscribe_addon(request):
    profile = request.user.individual_profile
    slug = request.POST.get('addon_slug', '')
    AddonSubscription.objects.filter(profile=profile, addon_slug=slug).update(status='cancelled')
    return JsonResponse({'ok': True})


# ── API Keys ─────────────────────────────────────────────────────────────────

@_individual_required
def api_keys_view(request):
    profile = request.user.individual_profile
    new_key_raw = None

    if request.method == 'POST':
        form = APIKeyForm(request.POST)
        if form.is_valid():
            if APIKey.objects.filter(profile=profile).count() >= 5:
                messages.error(request, 'Maximum 5 API keys allowed.')
            else:
                raw, prefix, hashed = APIKey.generate()
                APIKey.objects.create(
                    profile=profile,
                    name=form.cleaned_data['name'],
                    prefix=prefix,
                    hashed_key=hashed,
                )
                new_key_raw = raw
                messages.success(request, 'API key created. Copy it now — it won\'t be shown again.')
    else:
        form = APIKeyForm()

    keys = APIKey.objects.filter(profile=profile)
    ctx = {
        'form': form,
        'keys': keys,
        'new_key_raw': new_key_raw,
        'profile': profile,
    }
    return render(request, 'individual/api_keys.html', ctx)


@_individual_required
@require_POST
def revoke_api_key(request):
    profile = request.user.individual_profile
    key_id = request.POST.get('key_id')
    APIKey.objects.filter(profile=profile, id=key_id).update(is_active=False)
    return JsonResponse({'ok': True})


# ── Lightweight API Endpoint (for testing keys) ─────────────────────────────

def api_status(request):
    """Public endpoint: verify an API key and return account info."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return JsonResponse({'error': 'Missing Bearer token'}, status=401)

    raw_key = auth_header[7:]
    hashed = APIKey.hash_key(raw_key)

    _ensure_public_schema()
    try:
        key = APIKey.objects.select_related('profile__user').get(
            hashed_key=hashed, is_active=True,
        )
    except APIKey.DoesNotExist:
        return JsonResponse({'error': 'Invalid or revoked API key'}, status=401)

    # Update usage
    key.last_used_at = timezone.now()
    key.calls_today += 1
    key.calls_total += 1
    key.save(update_fields=['last_used_at', 'calls_today', 'calls_total'])

    subs = list(
        AddonSubscription.objects.filter(profile=key.profile, status='active')
        .values('addon_slug', 'plan')
    )
    return JsonResponse({
        'ok': True,
        'user': key.profile.user.get_full_name(),
        'email': key.profile.user.email,
        'key_name': key.name,
        'active_addons': subs,
    })
