import hashlib
import hmac
import json
import logging
import uuid
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from individual_users.forms import (
    APIKeyForm,
    EmailSigninForm,
    EmailSignupForm,
    PhoneSigninForm,
    PhoneSignupForm,
)
from individual_users.models import (
    AddonSubscription, APIKey, IndividualProfile, VerificationCode,
    ToolExamPaper, ToolLessonPlan, ToolQuestion,
)

logger = logging.getLogger(__name__)
User = get_user_model()


# ── Verification Helper ──────────────────────────────────────────────────────

def _send_verification_code(user, method):
    """Generate a 6-digit code, persist it, and deliver it."""
    import secrets as _secrets
    from django.core.mail import send_mail

    code = f"{_secrets.randbelow(1000000):06d}"
    VerificationCode.objects.filter(user=user, method=method).delete()
    VerificationCode.objects.create(
        user=user,
        code=code,
        method=method,
        expires_at=timezone.now() + timezone.timedelta(minutes=10),
    )

    if method == 'email' and user.email:
        send_mail(
            subject='Your Aura verification code',
            message=f'Your verification code is: {code}\n\nThis code expires in 10 minutes.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=_verification_email_html(code, user.first_name),
            fail_silently=True,
        )
    else:
        # Phone: send via WhatsApp (Africa's Talking), fall back to logging
        phone = getattr(user, 'phone', '') or ''
        if not phone:
            profile = IndividualProfile.objects.filter(user=user).first()
            phone = profile.phone_number if profile else ''
        if phone:
            try:
                from announcements.sms_service import send_whatsapp
                msg = (
                    f"Your Aura verification code is: *{code}*\n\n"
                    f"This code expires in 10 minutes. "
                    f"If you didn't create an Aura account, ignore this message."
                )
                result = send_whatsapp([phone], msg)
                if result.get('error'):
                    logger.warning('WhatsApp send failed for user %s: %s', user.pk, result['error'])
            except Exception:
                logger.exception('WhatsApp verification failed for user %s', user.pk)
        else:
            logger.warning('No phone number for user %s — cannot send verification', user.pk)


def _verification_email_html(code, first_name):
    """Minimal branded HTML email for the 6-digit verification code."""
    return (
        '<!DOCTYPE html><html><body style="margin:0;padding:0;font-family:Manrope,Arial,sans-serif;background:#f0f2f5">'
        '<table width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:40px 20px">'
        '<table width="480" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:16px;overflow:hidden">'
        '<tr><td style="background:linear-gradient(135deg,#0c0f1a,#4361ee);padding:32px;text-align:center">'
        '<span style="display:inline-block;width:44px;height:44px;background:rgba(255,255,255,.12);border-radius:12px;'
        'line-height:44px;color:#fff;font-weight:800;font-size:1.1rem">A</span>'
        '<h1 style="color:#fff;font-size:1.3rem;margin:12px 0 0">Verify your email</h1></td></tr>'
        f'<tr><td style="padding:32px">'
        f'<p style="color:#111827;font-size:.95rem;margin:0 0 8px">Hi {first_name},</p>'
        '<p style="color:#6b7280;font-size:.88rem;line-height:1.6;margin:0 0 24px">'
        'Enter this code to complete your Aura account setup:</p>'
        '<div style="text-align:center;margin:0 0 24px">'
        f'<span style="display:inline-block;letter-spacing:8px;font-size:2rem;font-weight:800;color:#4361ee;'
        f'background:#f0f2f5;padding:14px 28px;border-radius:12px">{code}</span></div>'
        '<p style="color:#6b7280;font-size:.82rem;margin:0">This code expires in <strong>10 minutes</strong>. '
        'If you didn\'t create an Aura account, you can safely ignore this email.</p>'
        '</td></tr>'
        '<tr><td style="padding:20px 32px;border-top:1px solid #e5e7eb;text-align:center">'
        '<p style="color:#9ca3af;font-size:.75rem;margin:0">Aura &mdash; School Management Platform</p>'
        '</td></tr></table></td></tr></table></body></html>'
    )


# ── Available Addons Catalog ─────────────────────────────────────────────────

ADDON_CATALOG = [
    {
        'slug': 'ai-tutor',
        'name': 'AI Tutor API',
        'icon': 'bi-robot',
        'description': 'Intelligent tutoring with adaptive learning paths, powered by GPT.',
        'plans': ['free', 'pro'],
        'category': 'ai',
        'prices': {'free': 0, 'pro': 49.99},
    },
    {
        'slug': 'grade-analytics',
        'name': 'Grade Analytics API',
        'icon': 'bi-graph-up-arrow',
        'description': 'Student performance analytics, trend detection, and grade prediction.',
        'plans': ['free', 'pro', 'enterprise'],
        'category': 'analytics',
        'prices': {'free': 0, 'pro': 39.99, 'enterprise': 99.99},
    },
    {
        'slug': 'attendance-tracker',
        'name': 'Attendance Tracker API',
        'icon': 'bi-calendar-check',
        'description': 'Real-time attendance tracking, absence alerts, and reporting.',
        'plans': ['free', 'pro'],
        'category': 'management',
        'prices': {'free': 0, 'pro': 29.99},
    },
    {
        'slug': 'lesson-planner',
        'name': 'Lesson Planner API',
        'icon': 'bi-journal-bookmark',
        'description': 'AI-generated lesson plans aligned to GES curriculum standards.',
        'plans': ['pro', 'enterprise'],
        'category': 'ai',
        'prices': {'pro': 59.99, 'enterprise': 149.99},
    },
    {
        'slug': 'exam-generator',
        'name': 'Exam Generator API',
        'icon': 'bi-file-earmark-text',
        'description': 'Auto-generate quizzes and exam papers from topics or syllabi.',
        'plans': ['pro', 'enterprise'],
        'category': 'ai',
        'prices': {'pro': 59.99, 'enterprise': 149.99},
    },
    {
        'slug': 'fee-manager',
        'name': 'Fee Management API',
        'icon': 'bi-cash-stack',
        'description': 'Fee structure creation, payment tracking, and receipt generation.',
        'plans': ['starter', 'pro'],
        'category': 'finance',
        'prices': {'starter': 19.99, 'pro': 49.99},
    },
    {
        'slug': 'sms-gateway',
        'name': 'SMS & Notification API',
        'icon': 'bi-chat-dots',
        'description': 'Send SMS alerts, push notifications, and email digests.',
        'plans': ['starter', 'pro', 'enterprise'],
        'category': 'communication',
        'prices': {'starter': 14.99, 'pro': 39.99, 'enterprise': 89.99},
    },
    {
        'slug': 'report-card',
        'name': 'Report Card API',
        'icon': 'bi-file-earmark-bar-graph',
        'description': 'Generate formatted PDF report cards with grade summaries.',
        'plans': ['pro', 'enterprise'],
        'category': 'documents',
        'prices': {'pro': 44.99, 'enterprise': 119.99},
    },
]


# ── Teacher Addon Catalog ─────────────────────────────────────────────────────
# Teachers see these tool-oriented addons instead of raw API products.

TEACHER_ADDON_CATALOG = [
    {
        'slug': 'exam-generator',
        'name': 'Question Bank & Exam Paper',
        'icon': 'bi-file-earmark-text',
        'description': 'Build a bank of questions by subject, topic and difficulty — then generate polished exam papers ready to print.',
        'plans': ['free', 'pro'],
        'category': 'assessment',
        'prices': {'free': 0, 'pro': 59.99},
    },
    {
        'slug': 'lesson-planner',
        'name': 'Smart Lesson Planner',
        'icon': 'bi-journal-bookmark',
        'description': 'Create structured lesson plans with AI or from scratch — aligned to GES curriculum standards.',
        'plans': ['free', 'pro'],
        'category': 'productivity',
        'prices': {'free': 0, 'pro': 59.99},
    },
    {
        'slug': 'ai-tutor',
        'name': 'AI Teaching Assistant',
        'icon': 'bi-robot',
        'description': 'AI-powered concept explainer, worksheet generator, marking helper and study notes creator.',
        'plans': ['free', 'pro'],
        'category': 'ai',
        'prices': {'free': 0, 'pro': 49.99},
    },
    {
        'slug': 'grade-analytics',
        'name': 'Grade Analytics',
        'icon': 'bi-graph-up-arrow',
        'description': 'Visualise student performance trends, class distributions and generate grade reports.',
        'plans': ['free', 'pro'],
        'category': 'analytics',
        'prices': {'free': 0, 'pro': 39.99},
    },
    {
        'slug': 'report-card',
        'name': 'Report Card Writer',
        'icon': 'bi-file-earmark-bar-graph',
        'description': 'Generate personalised report card comments with conduct and attitude ratings for each student.',
        'plans': ['free', 'pro'],
        'category': 'assessment',
        'prices': {'free': 0, 'pro': 44.99},
    },
    {
        'slug': 'attendance-tracker',
        'name': 'Attendance Tracker',
        'icon': 'bi-calendar-check',
        'description': 'Log daily attendance, detect absence patterns, and generate weekly/monthly reports.',
        'plans': ['free', 'pro'],
        'category': 'management',
        'prices': {'free': 0, 'pro': 29.99},
    },
    {
        'slug': 'slide-generator',
        'name': 'Slide Deck Generator',
        'icon': 'bi-easel',
        'description': 'Build beautiful Gamma-style presentations with AI — 8 themes, 7 layouts, fullscreen present mode and shareable links.',
        'plans': ['free', 'pro'],
        'category': 'productivity',
        'prices': {'free': 0, 'pro': 59.99},
    },
    {
        'slug': 'licensure-prep',
        'name': 'GTLE Licensure Prep',
        'icon': 'bi-mortarboard',
        'description': 'Prepare for the Ghana Teacher Licensure Examination with past questions, timed mock exams and AI-generated practice assessments.',
        'plans': ['free', 'pro'],
        'category': 'professional',
        'prices': {'free': 0, 'pro': 49.99},
    },
    {
        'slug': 'letter-writer',
        'name': 'GES Letter Writer',
        'icon': 'bi-envelope-paper',
        'description': 'Browse sample GES letters and generate official letters for transfers, leave, promotions, complaints and more.',
        'plans': ['free', 'pro'],
        'category': 'productivity',
        'prices': {'free': 0, 'pro': 39.99},
    },
    {
        'slug': 'paper-marker',
        'name': 'Paper Marker',
        'icon': 'bi-clipboard-check',
        'description': 'Mark objective question papers instantly — set an answer key, enter student responses, get auto-marked results with class analytics.',
        'plans': ['free', 'pro'],
        'category': 'assessment',
        'prices': {'free': 0, 'pro': 29.99},
    },
]


def _catalog_for_role(role):
    """Return the addon catalog appropriate for the user's role."""
    return TEACHER_ADDON_CATALOG if role == 'teacher' else ADDON_CATALOG


def _find_addon(slug):
    """Lookup an addon by slug across both catalogs."""
    for cat in (TEACHER_ADDON_CATALOG, ADDON_CATALOG):
        match = next((a for a in cat if a['slug'] == slug), None)
        if match:
            return match
    return None


def _get_role(request):
    """Get the role from query param, POST data, or profile."""
    role = request.POST.get('role') or request.GET.get('role', '')
    if role in ('teacher', 'developer'):
        return role
    if request.user.is_authenticated:
        try:
            return request.user.individual_profile.role
        except IndividualProfile.DoesNotExist:
            pass
    return 'developer'


def _ensure_public_schema():
    """Ensure we're operating on the public schema for individual user queries."""
    connection.set_schema_to_public()
    # Reset SCRIPT_NAME to ensure build_absolute_uri works correctly
    from django.urls import set_script_prefix
    set_script_prefix('')


def _individual_required(view_func):
    """Decorator: require login + user_type='individual' + verified."""
    from functools import wraps

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('individual:signin')
        if request.user.user_type != 'individual':
            messages.error(request, 'Access restricted to individual accounts.')
            return redirect('home')
        _ensure_public_schema()
        # Block unverified users
        profile = IndividualProfile.objects.filter(user=request.user).first()
        if profile and not profile.is_verified:
            method = 'phone' if (profile.phone_number and not request.user.email) else 'email'
            request.session['pending_verification_user_id'] = request.user.pk
            request.session['pending_verification_method'] = method
            logout(request)
            messages.info(request, 'Please verify your account to continue.')
            return redirect('individual:verify')
        return view_func(request, *args, **kwargs)

    return wrapper


# ── Auth Views ───────────────────────────────────────────────────────────────

def signup_view(request):
    """Combined signup page: Email / Phone / Google tabs."""
    if request.user.is_authenticated and request.user.user_type == 'individual':
        return redirect('individual:dashboard')

    _ensure_public_schema()
    role = _get_role(request)
    email_form = EmailSignupForm()
    phone_form = PhoneSignupForm()
    active_tab = 'email'
    method = request.POST.get('signup_method', '')

    if request.method == 'POST':
        role = request.POST.get('role', 'developer')
        if role not in ('developer', 'teacher'):
            role = 'developer'

        if method == 'email':
            active_tab = 'email'
            email_form = EmailSignupForm(request.POST)
            if email_form.is_valid():
                pw2 = request.POST.get('password2', '')
                if pw2 != email_form.cleaned_data['password']:
                    email_form.add_error('password', 'Passwords do not match.')
                else:
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
                    IndividualProfile.objects.create(user=user, role=role)
                    _send_verification_code(user, 'email')
                    request.session['pending_verification_user_id'] = user.pk
                    request.session['pending_verification_method'] = 'email'
                    return redirect('individual:verify')

        elif method == 'phone':
            active_tab = 'phone'
            phone_form = PhoneSignupForm(request.POST)
            if phone_form.is_valid():
                pw2 = request.POST.get('password2', '')
                if pw2 != phone_form.cleaned_data['password']:
                    phone_form.add_error('password', 'Passwords do not match.')
                else:
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
                    IndividualProfile.objects.create(user=user, phone_number=phone, role=role)
                    _send_verification_code(user, 'phone')
                    request.session['pending_verification_user_id'] = user.pk
                    request.session['pending_verification_method'] = 'phone'
                    return redirect('individual:verify')

    ctx = {
        'email_form': email_form,
        'phone_form': phone_form,
        'active_tab': active_tab,
        'google_client_id': getattr(settings, 'GOOGLE_OAUTH_CLIENT_ID', ''),
        'role': role,
    }
    return render(request, 'individual/auth.html', ctx)


# ── Verification Views ───────────────────────────────────────────────────────

def verify_view(request):
    """Show the 6-digit code form and validate on POST."""
    _ensure_public_schema()
    user_id = request.session.get('pending_verification_user_id')
    method = request.session.get('pending_verification_method', 'email')

    if not user_id:
        return redirect('individual:signup')

    try:
        user = User.objects.get(pk=user_id, user_type='individual')
    except User.DoesNotExist:
        request.session.pop('pending_verification_user_id', None)
        return redirect('individual:signup')

    profile = IndividualProfile.objects.filter(user=user).first()

    # Build a masked contact string
    if method == 'email':
        email = user.email
        local, domain = email.split('@') if '@' in email else (email, '')
        masked = local[:2] + '***@' + domain if domain else email
    else:
        phone = profile.phone_number if profile else ''
        masked = phone[:4] + '****' + phone[-2:] if len(phone) > 6 else phone

    error = ''
    if request.method == 'POST':
        entered_code = request.POST.get('code', '').strip()
        vc = VerificationCode.objects.filter(
            user=user, method=method,
        ).order_by('-created_at').first()

        if not vc:
            error = 'No verification code found. Please request a new one.'
        elif vc.is_expired():
            error = 'Code expired. Please request a new one.'
        elif vc.attempts >= 5:
            error = 'Too many attempts. Please request a new code.'
        elif vc.code != entered_code:
            vc.attempts += 1
            vc.save(update_fields=['attempts'])
            remaining = 5 - vc.attempts
            error = f'Invalid code. {remaining} attempt{"s" if remaining != 1 else ""} remaining.'
        else:
            # Correct code — mark verified, log in
            if profile:
                if method == 'email':
                    profile.email_verified = True
                else:
                    profile.phone_verified = True
                profile.save(update_fields=['email_verified', 'phone_verified'])
            vc.delete()

            request.session.pop('pending_verification_user_id', None)
            request.session.pop('pending_verification_method', None)

            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            request.session.pop('auth_tenant_schema', None)
            messages.success(request, f'Welcome, {user.first_name}! Your account is verified.')
            return redirect('individual:dashboard')

    ctx = {
        'method': method,
        'masked_contact': masked,
        'error': error,
        'role': profile.role if profile else 'developer',
    }
    return render(request, 'individual/verify.html', ctx)


@require_POST
def resend_code_view(request):
    """Regenerate and resend a verification code (rate-limited to 60 s)."""
    _ensure_public_schema()
    user_id = request.session.get('pending_verification_user_id')
    method = request.session.get('pending_verification_method', 'email')

    if not user_id:
        return redirect('individual:signup')

    try:
        user = User.objects.get(pk=user_id, user_type='individual')
    except User.DoesNotExist:
        return redirect('individual:signup')

    last = VerificationCode.objects.filter(
        user=user, method=method,
    ).order_by('-created_at').first()

    if last and (timezone.now() - last.created_at).total_seconds() < 60:
        messages.error(request, 'Please wait a moment before requesting a new code.')
        return redirect('individual:verify')

    _send_verification_code(user, method)
    messages.success(request, 'A new verification code has been sent.')
    return redirect('individual:verify')


def signin_view(request):
    """Combined signin page: Email / Phone / Google tabs."""
    if request.user.is_authenticated and request.user.user_type == 'individual':
        return redirect('individual:dashboard')

    _ensure_public_schema()
    role = _get_role(request)
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
                    profile = IndividualProfile.objects.filter(user=user).first()
                    if profile and not profile.email_verified and not profile.google_id:
                        _send_verification_code(user, 'email')
                        request.session['pending_verification_user_id'] = user.pk
                        request.session['pending_verification_method'] = 'email'
                        return redirect('individual:verify')
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
                    profile = IndividualProfile.objects.filter(user=user).first()
                    if profile and not profile.phone_verified and profile.phone_number and not profile.google_id:
                        _send_verification_code(user, 'phone')
                        request.session['pending_verification_user_id'] = user.pk
                        request.session['pending_verification_method'] = 'phone'
                        return redirect('individual:verify')
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
        'role': role,
    }
    return render(request, 'individual/auth.html', ctx)


def google_auth_view(request):
    """Initiate Google OAuth 2.0 — redirect to Google's consent screen.

    This replaces the old GIS client-library approach (prompt / renderButton)
    which fails with a blank page and postMessage errors in many browsers.
    The standard server-side code flow works everywhere.
    """
    _ensure_public_schema()

    import secrets
    from urllib.parse import urlencode

    client_id = getattr(settings, 'GOOGLE_OAUTH_CLIENT_ID', '')
    if not client_id:
        messages.error(request, 'Google sign-in is not configured.')
        return redirect('individual:signin')

    # Preserve role for the callback
    role = request.GET.get('role', 'developer')
    request.session['_google_role'] = role

    # CSRF state token
    state = secrets.token_urlsafe(32)
    request.session['_google_state'] = state

    callback_url = request.build_absolute_uri('/u/auth/google/callback/')

    params = urlencode({
        'client_id': client_id,
        'redirect_uri': callback_url,
        'response_type': 'code',
        'scope': 'openid email profile',
        'access_type': 'online',
        'state': state,
        'prompt': 'select_account',
    })
    return redirect(f'https://accounts.google.com/o/oauth2/v2/auth?{params}')


def google_callback_view(request):
    """Handle the OAuth 2.0 callback from Google — exchange code for tokens."""
    _ensure_public_schema()

    import urllib.request
    import urllib.parse

    # ── Extract callback parameters ───────────────────────────────
    error = request.GET.get('error', '')
    if error:
        logger.warning(f'Google OAuth error: {error}')
        messages.error(request, 'Google sign-in was cancelled or failed.')
        return redirect('individual:signin')

    code = request.GET.get('code', '')
    state = request.GET.get('state', '')

    if not code:
        logger.error('No authorization code in Google callback')
        messages.error(request, 'Authorization code not received from Google.')
        return redirect('individual:signin')

    # Verify CSRF state
    expected_state = request.session.pop('_google_state', None)
    if not state or state != expected_state:
        logger.error('Google OAuth state mismatch')
        messages.error(request, 'Security check failed. Please try again.')
        return redirect('individual:signin')

    client_id = getattr(settings, 'GOOGLE_OAUTH_CLIENT_ID', '')
    client_secret = getattr(settings, 'GOOGLE_OAUTH_CLIENT_SECRET', '')
    if not client_id or not client_secret:
        logger.error('Google OAuth credentials not configured')
        messages.error(request, 'Google sign-in is misconfigured.')
        return redirect('individual:signin')

    callback_url = request.build_absolute_uri('/u/auth/google/callback/')

    # ── Exchange code → tokens ────────────────────────────────────
    token_data_bytes = urllib.parse.urlencode({
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': callback_url,
        'grant_type': 'authorization_code',
    }).encode()

    try:
        token_req = urllib.request.Request(
            'https://oauth2.googleapis.com/token',
            data=token_data_bytes,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
        )
        with urllib.request.urlopen(token_req, timeout=10) as resp:
            token_data = json.loads(resp.read())
    except Exception as e:
        logger.exception(f'Google token exchange failed: {e}')
        messages.error(request, 'Could not verify Google credentials.')
        return redirect('individual:signin')

    logger.info(f'Google token exchange response: {token_data.keys()}')
    id_token_jwt = token_data.get('id_token')
    if not id_token_jwt:
        logger.error(f'No id_token in response: {token_data}')
        messages.error(request, 'Google sign-in failed — no ID token.')
        return redirect('individual:signin')

    # ── Verify ID token ───────────────────────────────────────────
    # Use Google's tokeninfo endpoint for server-side verification.
    # This avoids needing cryptography/google-auth for local RSA ops.
    try:
        tokeninfo_url = f'https://oauth2.googleapis.com/tokeninfo?id_token={urllib.parse.quote(id_token_jwt)}'
        tokeninfo_req = urllib.request.Request(tokeninfo_url)
        with urllib.request.urlopen(tokeninfo_req, timeout=10) as resp:
            idinfo = json.loads(resp.read())

        # Verify audience matches our client ID
        if idinfo.get('aud') != client_id:
            raise ValueError(f"Token audience {idinfo.get('aud')} doesn't match client ID")

        # Verify issuer
        if idinfo.get('iss') not in ('https://accounts.google.com', 'accounts.google.com'):
            raise ValueError(f"Invalid issuer: {idinfo.get('iss')}")

    except Exception as e:
        logger.exception(f'Google token verification failed: {e}')
        messages.error(request, 'Google sign-in failed. Please try again.')
        return redirect('individual:signin')

    google_id = idinfo['sub']
    email = idinfo.get('email', '')
    name = idinfo.get('name', '')
    picture = idinfo.get('picture', '')

    # ── Find or create user ───────────────────────────────────────
    profile = IndividualProfile.objects.filter(
        google_id=google_id,
    ).select_related('user').first()

    if profile:
        user = profile.user
    else:
        existing = User.objects.filter(email=email, user_type='individual').first()
        if existing:
            profile, _ = IndividualProfile.objects.get_or_create(user=existing)
            profile.google_id = google_id
            profile.avatar_url = picture
            profile.email_verified = True
            profile.save()
            user = existing
        else:
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

            role = request.session.pop('_google_role', 'developer')
            IndividualProfile.objects.create(
                user=user, google_id=google_id, avatar_url=picture,
                email_verified=True,
                role=role if role in ('teacher', 'developer') else 'developer',
            )

    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    request.session.pop('auth_tenant_schema', None)
    return redirect('individual:dashboard')


def signout_view(request):
    logout(request)
    return redirect('individual:signin')


# ── Teacher Shortcut Redirects ───────────────────────────────────────────────

def teacher_redirect(request):
    """Redirect /t/ and /t/signup/ to /u/signup/?role=teacher."""
    return redirect('/u/signup/?role=teacher')


def teacher_signin_redirect(request):
    """Redirect /t/signin/ to /u/signin/?role=teacher."""
    return redirect('/u/signin/?role=teacher')


# ── Dashboard ────────────────────────────────────────────────────────────────

@_individual_required
def dashboard_view(request):
    profile, _ = IndividualProfile.objects.get_or_create(user=request.user)
    subscriptions = AddonSubscription.objects.filter(profile=profile, status='active')
    api_keys = APIKey.objects.filter(profile=profile)
    total_calls = sum(k.calls_total for k in api_keys)
    active_keys = api_keys.filter(is_active=True).count()

    # Teacher-specific: recommend addons + tool stats + my addons with URLs
    recommended = []
    tool_stats = {}
    my_addons = []
    if profile.role == 'teacher':
        my_slugs = set(subscriptions.values_list('addon_slug', flat=True))
        recommended = [a for a in TEACHER_ADDON_CATALOG if a['slug'] not in my_slugs][:4]
        tool_stats = {
            'questions': ToolQuestion.objects.filter(profile=profile).count(),
            'exams': ToolExamPaper.objects.filter(profile=profile).count(),
            'lessons': ToolLessonPlan.objects.filter(profile=profile).count(),
        }
        # Build subscribed addons with icons and URL names for the dashboard
        _ADDON_URL_MAP = {
            'exam-generator': 'individual:question_bank',
            'lesson-planner': 'individual:lesson_plans',
            'slide-generator': 'individual:deck_list',
            'licensure-prep': 'individual:licensure_dashboard',
            'ai-tutor': 'individual:ai_tutor_dashboard',
            'letter-writer': 'individual:letter_dashboard',
            'paper-marker': 'individual:marker_dashboard',
            'report-card': 'individual:report_card_dashboard',
        }
        _ADDON_COLORS = {
            'exam-generator': '#4361ee',
            'lesson-planner': '#059669',
            'slide-generator': '#7c3aed',
            'licensure-prep': '#0d9488',
            'ai-tutor': '#0891b2',
            'grade-analytics': '#7c3aed',
            'report-card': '#d97706',
            'attendance-tracker': '#dc2626',
            'letter-writer': '#2563eb',
            'paper-marker': '#e11d48',
        }
        catalog_map = {a['slug']: a for a in TEACHER_ADDON_CATALOG}
        for sub in subscriptions:
            cat = catalog_map.get(sub.addon_slug)
            if cat:
                my_addons.append({
                    'name': cat['name'],
                    'icon': cat['icon'],
                    'slug': sub.addon_slug,
                    'color': _ADDON_COLORS.get(sub.addon_slug, '#4361ee'),
                    'url_name': _ADDON_URL_MAP.get(sub.addon_slug, ''),
                })

    ctx = {
        'profile': profile,
        'role': profile.role,
        'subscriptions': subscriptions,
        'subscription_count': subscriptions.count(),
        'api_keys': api_keys,
        'api_key_count': active_keys,
        'total_api_calls': total_calls,
        'addon_catalog': _catalog_for_role(profile.role),
        'catalog_count': len(_catalog_for_role(profile.role)),
        'recommended_addons': recommended,
        'tool_stats': tool_stats,
        'my_addons': my_addons,
    }
    return render(request, 'individual/dashboard.html', ctx)


# ── Settings ─────────────────────────────────────────────────────────────────

@_individual_required
def settings_view(request):
    """Account & profile settings for individual users."""
    profile, _ = IndividualProfile.objects.get_or_create(user=request.user)
    user = request.user

    if request.method == 'POST':
        section = request.POST.get('section', 'profile')

        if section == 'profile':
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            phone = request.POST.get('phone_number', '').strip()
            company = request.POST.get('company', '').strip()
            bio = request.POST.get('bio', '').strip()

            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
            user.save(update_fields=['first_name', 'last_name'])

            profile.phone_number = phone
            profile.company = company
            profile.bio = bio
            profile.save(update_fields=['phone_number', 'company', 'bio'])
            messages.success(request, 'Profile updated.')

        elif section == 'password':
            current = request.POST.get('current_password', '')
            new1 = request.POST.get('new_password', '')
            new2 = request.POST.get('confirm_password', '')
            if not user.check_password(current):
                messages.error(request, 'Current password is incorrect.')
            elif len(new1) < 8:
                messages.error(request, 'New password must be at least 8 characters.')
            elif new1 != new2:
                messages.error(request, 'New passwords do not match.')
            else:
                user.set_password(new1)
                user.save()
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed.')

        return redirect('individual:settings')

    ctx = {
        'profile': profile,
        'role': profile.role,
    }
    return render(request, 'individual/settings.html', ctx)


# ── Addon Marketplace ────────────────────────────────────────────────────────

@_individual_required
def addons_view(request):
    profile = request.user.individual_profile
    my_slugs = set(
        AddonSubscription.objects.filter(profile=profile, status='active')
        .values_list('addon_slug', flat=True)
    )
    source_catalog = _catalog_for_role(profile.role)
    catalog = []
    for addon in source_catalog:
        prices = addon.get('prices', {})
        first_plan = addon['plans'][0] if addon['plans'] else 'free'
        catalog.append({
            **addon,
            'subscribed': addon['slug'] in my_slugs,
            'prices_json': json.dumps(prices),
            'first_price': prices.get(first_plan, 0),
        })

    ctx = {
        'catalog': catalog,
        'profile': profile,
        'role': profile.role,
        'categories': sorted({a['category'] for a in source_catalog}),
        'currency': getattr(settings, 'PAYSTACK_CURRENCY', 'GHS'),
    }
    return render(request, 'individual/addons.html', ctx)


@_individual_required
@require_POST
def subscribe_addon(request):
    profile = request.user.individual_profile
    slug = request.POST.get('addon_slug', '')
    plan = request.POST.get('plan', 'free')

    addon = _find_addon(slug)
    if not addon:
        return JsonResponse({'error': 'Addon not found'}, status=404)
    if plan not in addon['plans']:
        return JsonResponse({'error': 'Plan not available for this addon'}, status=400)

    price = addon.get('prices', {}).get(plan, 0)

    if price <= 0:
        # Free plan: activate immediately
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

    # Paid plan: return Paystack params for inline popup
    ref = f"IU-{request.user.id}-{slug}-{plan}-{uuid.uuid4().hex[:8]}"
    return JsonResponse({
        'paystack': True,
        'public_key': settings.PAYSTACK_PUBLIC_KEY,
        'email': request.user.email or f'{request.user.username}@aura.local',
        'amount': int(Decimal(str(price)) * 100),  # pesewas/kobo
        'currency': getattr(settings, 'PAYSTACK_CURRENCY', 'GHS'),
        'reference': ref,
        'addon_name': addon['name'],
        'addon_slug': slug,
        'plan': plan,
    })


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
        'role': profile.role,
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


# ── Paystack Payment Verification ───────────────────────────────────────────

@_individual_required
@require_POST
def verify_addon_payment(request):
    """Verify a Paystack payment and activate a paid addon subscription."""
    import requests as http_requests

    _ensure_public_schema()
    profile = request.user.individual_profile

    body = json.loads(request.body) if request.content_type == 'application/json' else request.POST
    reference = body.get('reference', '')
    slug = body.get('addon_slug', '')
    plan = body.get('plan', '')

    if not reference or not slug:
        return JsonResponse({'ok': False, 'error': 'Missing data'}, status=400)

    addon = _find_addon(slug)
    if not addon:
        return JsonResponse({'ok': False, 'error': 'Addon not found'}, status=404)

    # Verify with Paystack API
    secret = settings.PAYSTACK_SECRET_KEY
    if secret:
        resp = http_requests.get(
            f'https://api.paystack.co/transaction/verify/{reference}',
            headers={'Authorization': f'Bearer {secret}'},
            timeout=15,
        )
        data = resp.json()
        if not data.get('status') or data.get('data', {}).get('status') != 'success':
            return JsonResponse({'ok': False, 'error': 'Payment verification failed'}, status=402)
        amount_paid = Decimal(str(data['data']['amount'])) / 100
    else:
        # Dev mode: no Paystack key — accept at face value
        amount_paid = Decimal(str(addon.get('prices', {}).get(plan, 0)))

    sub, created = AddonSubscription.objects.update_or_create(
        profile=profile, addon_slug=slug,
        defaults={
            'addon_name': addon['name'],
            'plan': plan or addon['plans'][0],
            'status': 'active',
            'expires_at': None,
            'payment_reference': reference,
            'amount_paid': amount_paid,
        },
    )
    return JsonResponse({'ok': True, 'addon': addon['name']})


@csrf_exempt
def paystack_individual_webhook(request):
    """Paystack webhook for individual user addon payments. HMAC-verified."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)

    secret = getattr(settings, 'PAYSTACK_SECRET_KEY', '')
    sig = request.headers.get('X-Paystack-Signature', '')
    expected = hmac.new(secret.encode(), request.body, hashlib.sha512).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return JsonResponse({'error': 'Bad signature'}, status=403)

    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Bad JSON'}, status=400)

    event = payload.get('event')
    data = payload.get('data', {})

    if event == 'charge.success':
        reference = data.get('reference', '')
        if reference.startswith('IU-'):
            _handle_individual_addon_payment(reference, data)

    return JsonResponse({'ok': True})


def _handle_individual_addon_payment(reference, data):
    """Activate an individual addon subscription from a confirmed Paystack charge."""
    _ensure_public_schema()

    # Parse reference: IU-{user_id}-{slug}-{plan}-{uuid}
    parts = reference.split('-', 4)
    if len(parts) < 4:
        return

    try:
        user_id = int(parts[1])
    except (ValueError, IndexError):
        return

    slug = parts[2]
    plan = parts[3] if len(parts) > 3 else 'pro'

    try:
        user = User.objects.get(id=user_id, user_type='individual')
        profile = user.individual_profile
    except (User.DoesNotExist, IndividualProfile.DoesNotExist):
        return

    addon = _find_addon(slug)
    if not addon:
        return

    # Deduplicate by payment_reference
    if AddonSubscription.objects.filter(payment_reference=reference).exists():
        return

    amount_paid = Decimal(str(data.get('amount', 0))) / 100

    AddonSubscription.objects.update_or_create(
        profile=profile, addon_slug=slug,
        defaults={
            'addon_name': addon['name'],
            'plan': plan,
            'status': 'active',
            'expires_at': None,
            'payment_reference': reference,
            'amount_paid': amount_paid,
        },
    )
