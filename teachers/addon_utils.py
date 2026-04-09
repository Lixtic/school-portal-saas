"""Utilities for teacher add-on feature gating (credit-based token model)."""
from functools import wraps

from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect
from django.utils import timezone


# ── Credit costs per AI action ──────────────────────────────────
CREDIT_COSTS = {
    'lesson_gen':     1,
    'exercise_gen':   1,
    'assignment_gen': 1,
    'study_guide':    2,
    'slide_gen':      3,
    'bulk_gen':       5,
    'report_card':    2,
    'question_gen':   2,
    'differentiate':  2,
    'other':          1,
}

WELCOME_BONUS_CREDITS = 10


# ── Add-on slug → gated view names ─────────────────────────────
ADDON_FEATURE_MAP = {
    'padi-slide-generator': {
        'label': 'SchoolPadi Slide Generator',
        'gates': [
            'presentation_api',
            'presentation_generate_from_doc', 'presentation_from_youtube',
            'presentation_generate_image',
        ],
    },
    'smart-planner-pro': {
        'label': 'Smart Planner Pro',
        'gates': [
            'padi_t_api', 'ges_lesson_api', 'ges_weekly_batch_api',
        ],
    },
    'exercise-maker': {
        'label': 'Exercise Maker',
        'gates': ['manage_exercises'],
    },
    'grade-insight-dashboard': {
        'label': 'Grade Insight Dashboard',
        'gates': ['analytics_dashboard', 'boost_intervention', 'generate_remedial_lesson'],
    },
    'quick-report-writer': {
        'label': 'Quick Report Writer',
        'gates': ['lesson_plan_pdf', 'lesson_plan_cards_print'],
    },
    'task-board': {
        'label': 'Task Board',
        'gates': ['addon_task_board'],
    },
    'cpd-tracker': {
        'label': 'CPD Tracker',
        'gates': ['addon_cpd_tracker'],
    },
    'observation-notes': {
        'label': 'Observation Notes',
        'gates': ['addon_observation_notes'],
    },
    'rubric-designer': {
        'label': 'Rubric Designer',
        'gates': ['addon_rubric_designer'],
    },
    'study-guide-builder': {
        'label': 'Study Guide Builder',
        'gates': ['study_guide_ai'],
    },
    'random-picker': {
        'label': 'Random Picker',
        'gates': ['addon_random_picker'],
    },
    'countdown-timer': {
        'label': 'Countdown Timer',
        'gates': ['addon_countdown_timer'],
    },
    'noise-meter': {
        'label': 'Noise Meter',
        'gates': ['addon_noise_meter'],
    },
    'stem-activity-pack': {
        'label': 'STEM Activity Pack',
        'gates': ['addon_stem_pack'],
    },
    'creative-arts-kit': {
        'label': 'Creative Arts Kit',
        'gates': ['addon_creative_arts'],
    },
    'report-card-writer': {
        'label': 'Report Card AI Writer',
        'gates': ['report_card_ai'],
    },
    'exam-question-bank': {
        'label': 'Exam & Question Bank Pro',
        'gates': ['question_bank_ai'],
    },
    'behavior-sel-tracker': {
        'label': 'Behavior & SEL Tracker',
        'gates': ['addon_behavior_tracker'],
    },
    'differentiated-lesson-ai': {
        'label': 'Differentiated Lesson AI',
        'gates': ['differentiated_ai'],
    },
    'live-quiz-engine': {
        'label': 'Live Quiz Engine',
        'gates': ['addon_live_quiz'],
    },
    'attendance-tracker': {
        'label': 'Attendance Tracker',
        'gates': ['addon_attendance_tracker'],
    },
}

# Reverse map: view_name → addon_slug
VIEW_ADDON_MAP = {}
for _slug, _info in ADDON_FEATURE_MAP.items():
    for _view in _info['gates']:
        VIEW_ADDON_MAP[_view] = _slug


def has_addon(user, slug):
    """Return True if *user* has an active, non-expired purchase for the add-on *slug*."""
    if not user.is_authenticated or user.user_type != 'teacher':
        return False
    from teachers.models import TeacherAddOnPurchase
    from django.db.models import Q
    now = timezone.now()
    return TeacherAddOnPurchase.objects.filter(
        Q(expires_at__isnull=True) | Q(expires_at__gt=now),
        teacher=user, addon__slug=slug, is_active=True,
    ).exists()


def get_purchased_slugs(user):
    """Return a set of active, non-expired add-on slugs for the given teacher."""
    if not user.is_authenticated or user.user_type != 'teacher':
        return set()
    from teachers.models import TeacherAddOnPurchase
    from django.db.models import Q
    now = timezone.now()
    return set(
        TeacherAddOnPurchase.objects.filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now),
            teacher=user, is_active=True,
        ).values_list('addon__slug', flat=True)
    )


def requires_addon(slug):
    """Decorator that gates a view behind an active add-on purchase."""
    def decorator(view_fn):
        @wraps(view_fn)
        def wrapper(request, *args, **kwargs):
            if request.user.user_type != 'teacher':
                # Non-teachers (admins) bypass add-on checks
                return view_fn(request, *args, **kwargs)
            if has_addon(request.user, slug):
                return view_fn(request, *args, **kwargs)
            label = ADDON_FEATURE_MAP.get(slug, {}).get('label', slug)
            messages.warning(
                request,
                f'This feature requires the "{label}" add-on. '
                f'Visit the Add-on Store to activate it.',
            )
            return redirect('teachers:teacher_store')
        return wrapper
    return decorator


# ── Freemium gating (credit-based token model) ─────────────────

FREE_GENERATION_LIMIT = WELCOME_BONUS_CREDITS  # backward compat alias


def _get_or_create_balance(user):
    """Return the TeacherCreditBalance for *user*, creating with welcome bonus if new."""
    from teachers.models import TeacherCreditBalance, CreditTransaction
    bal, created = TeacherCreditBalance.objects.get_or_create(
        teacher=user,
        defaults={'balance': WELCOME_BONUS_CREDITS, 'total_purchased': 0, 'total_used': 0},
    )
    if created:
        CreditTransaction.objects.create(
            teacher=user,
            amount=WELCOME_BONUS_CREDITS,
            balance_after=WELCOME_BONUS_CREDITS,
            transaction_type='bonus',
            description=f'Welcome bonus — {WELCOME_BONUS_CREDITS} free AI credits',
        )
    return bal


def get_credit_balance(user):
    """Return the current credit balance for *user*."""
    if not user.is_authenticated or user.user_type != 'teacher':
        return 0
    bal = _get_or_create_balance(user)
    return bal.balance


def get_free_generation_count(user, action_type='lesson_gen'):
    """Backward-compat: returns how many credits have been used (for UI display)."""
    if not user.is_authenticated:
        return 0
    bal = _get_or_create_balance(user)
    return bal.total_used


def deduct_credits(user, action_type, description=''):
    """Deduct credits for an AI action. Returns (success, error_dict_or_None)."""
    from teachers.models import TeacherCreditBalance, CreditTransaction
    cost = CREDIT_COSTS.get(action_type, 1)

    with transaction.atomic():
        bal = TeacherCreditBalance.objects.select_for_update().get(teacher=user)
        if bal.balance < cost:
            return False, {
                'status': 'error',
                'error_code': 'insufficient_credits',
                'message': (
                    f'You need {cost} credit{"s" if cost != 1 else ""} for this action '
                    f'but only have {bal.balance}. Buy more credits from the Add-on Store.'
                ),
                'balance': bal.balance,
                'cost': cost,
            }
        bal.balance -= cost
        bal.total_used += cost
        bal.save(update_fields=['balance', 'total_used', 'updated_at'])

        action_label = action_type.replace('_', ' ').title()
        CreditTransaction.objects.create(
            teacher=user,
            amount=-cost,
            balance_after=bal.balance,
            transaction_type='usage',
            description=description or f'{action_label} (-{cost} credit{"s" if cost != 1 else ""})',
        )
    return True, None


def add_credits(user, amount, transaction_type='purchase', description='', payment_reference=''):
    """Add credits to a teacher's balance."""
    from teachers.models import TeacherCreditBalance, CreditTransaction

    with transaction.atomic():
        bal = _get_or_create_balance(user)
        bal = TeacherCreditBalance.objects.select_for_update().get(teacher=user)
        bal.balance += amount
        if transaction_type == 'purchase':
            bal.total_purchased += amount
        bal.save(update_fields=['balance', 'total_purchased', 'updated_at'])

        CreditTransaction.objects.create(
            teacher=user,
            amount=amount,
            balance_after=bal.balance,
            transaction_type=transaction_type,
            description=description,
            payment_reference=payment_reference,
        )
    return bal


def check_freemium_limit(user, slug, action_type='lesson_gen', free_limit=FREE_GENERATION_LIMIT):
    """Check if teacher has enough credits for this action, then deduct.

    Returns (allowed, error_dict_or_None).
    """
    if getattr(user, 'user_type', '') != 'teacher':
        return True, None

    # Ensure balance exists (welcome bonus applied on first check)
    _get_or_create_balance(user)

    # Attempt to deduct credits
    return deduct_credits(user, action_type)


def requires_addon_freemium(slug, free_limit=FREE_GENERATION_LIMIT, action_type='lesson_gen'):
    """Decorator: check teacher has enough credits, deduct on entry.

    For AJAX/JSON endpoints: returns a JSON 403 with balance info.
    For regular views: redirects to the store with a flash message.
    """
    def decorator(view_fn):
        @wraps(view_fn)
        def wrapper(request, *args, **kwargs):
            if request.user.user_type != 'teacher':
                return view_fn(request, *args, **kwargs)

            # Ensure balance exists
            _get_or_create_balance(request.user)

            cost = CREDIT_COSTS.get(action_type, 1)
            bal = get_credit_balance(request.user)

            if bal >= cost:
                # Deduct credits and proceed
                ok, err = deduct_credits(request.user, action_type)
                if ok:
                    return view_fn(request, *args, **kwargs)
                # Shouldn't happen (race condition), but handle
                err_msg = err.get('message', 'Insufficient credits.')
            else:
                err_msg = (
                    f'This action costs {cost} credit{"s" if cost != 1 else ""} '
                    f'but you only have {bal}. Buy more credits from the Add-on Store.'
                )

            is_ajax = (
                request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                or request.content_type == 'application/json'
            )
            if is_ajax:
                from django.http import JsonResponse
                return JsonResponse({
                    'status': 'error',
                    'error_code': 'insufficient_credits',
                    'message': err_msg,
                    'balance': get_credit_balance(request.user),
                    'cost': cost,
                }, status=403)
            messages.warning(request, err_msg)
            return redirect('teachers:teacher_store')
        return wrapper
    return decorator
