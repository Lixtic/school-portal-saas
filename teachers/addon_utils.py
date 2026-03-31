"""Utilities for teacher add-on feature gating."""
from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect
from django.utils import timezone


# ── Add-on slug → gated view names ─────────────────────────────
ADDON_FEATURE_MAP = {
    'aura-slide-generator': {
        'label': 'Aura Slide Generator',
        'gates': [
            'presentation_api',
            'presentation_generate_from_doc', 'presentation_from_youtube',
            'presentation_generate_image',
        ],
    },
    'smart-planner-pro': {
        'label': 'Smart Planner Pro',
        'gates': [
            'aura_t_api', 'ges_lesson_api',
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


# ── Freemium gating ─────────────────────────────────────────────

FREE_GENERATION_LIMIT = 10


def get_free_generation_count(user, action_type='lesson_gen'):
    """Count how many AI generation calls this teacher has made (all-time)."""
    if not user.is_authenticated:
        return 0
    try:
        from tenants.subscription_models import AIUsageLog
        return AIUsageLog.objects.filter(
            user_id=user.id, action_type=action_type,
        ).count()
    except Exception:
        return 0


def check_freemium_limit(user, slug, action_type='lesson_gen', free_limit=FREE_GENERATION_LIMIT):
    """Inline freemium check. Returns (allowed, error_dict_or_None).

    Use inside multi-action views where a decorator can't target one branch.
    If ``allowed`` is False, return ``JsonResponse(err, status=403)`` to the client.
    """
    if getattr(user, 'user_type', '') != 'teacher':
        return True, None
    if has_addon(user, slug):
        return True, None
    used = get_free_generation_count(user, action_type)
    if used < free_limit:
        return True, None
    label = ADDON_FEATURE_MAP.get(slug, {}).get('label', slug)
    return False, {
        'status': 'error',
        'error_code': 'freemium_limit',
        'message': (
            f'You\'ve used all {free_limit} free generations. '
            f'Purchase "{label}" from the Add-on Store to continue.'
        ),
        'used': used,
        'limit': free_limit,
    }


def requires_addon_freemium(slug, free_limit=FREE_GENERATION_LIMIT, action_type='lesson_gen'):
    """Decorator: allow *free_limit* free generations, then require the add-on.

    For AJAX/JSON endpoints: returns a JSON 403 with remaining/used counts.
    For regular views: redirects to the store with a flash message.
    """
    def decorator(view_fn):
        @wraps(view_fn)
        def wrapper(request, *args, **kwargs):
            if request.user.user_type != 'teacher':
                return view_fn(request, *args, **kwargs)
            if has_addon(request.user, slug):
                return view_fn(request, *args, **kwargs)
            # Check free-tier budget
            used = get_free_generation_count(request.user, action_type)
            if used < free_limit:
                return view_fn(request, *args, **kwargs)
            # Over free limit — block
            label = ADDON_FEATURE_MAP.get(slug, {}).get('label', slug)
            is_ajax = (
                request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                or request.content_type == 'application/json'
            )
            if is_ajax:
                from django.http import JsonResponse
                return JsonResponse({
                    'status': 'error',
                    'error_code': 'freemium_limit',
                    'message': (
                        f'You\'ve used all {free_limit} free generations. '
                        f'Purchase "{label}" from the Add-on Store to continue.'
                    ),
                    'used': used,
                    'limit': free_limit,
                }, status=403)
            messages.warning(
                request,
                f'You\'ve used all {free_limit} free lesson generations. '
                f'Purchase "{label}" from the Add-on Store to unlock unlimited access.',
            )
            return redirect('teachers:teacher_store')
        return wrapper
    return decorator
