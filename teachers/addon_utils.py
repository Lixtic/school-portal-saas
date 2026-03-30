"""Utilities for teacher add-on feature gating."""
from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


# ── Add-on slug → gated view names ─────────────────────────────
ADDON_FEATURE_MAP = {
    'aura-slide-generator': {
        'label': 'Aura Slide Generator',
        'gates': [
            'presentation_create', 'presentation_api',
            'presentation_generate_from_doc', 'presentation_from_youtube',
            'presentation_generate_image',
        ],
    },
    'smart-planner-pro': {
        'label': 'Smart Planner Pro',
        'gates': [
            'aura_command_center', 'aura_t_api', 'ges_lesson_api',
            'save_aura_t_plan', 'aura_flight_manual',
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
}

# Reverse map: view_name → addon_slug
VIEW_ADDON_MAP = {}
for _slug, _info in ADDON_FEATURE_MAP.items():
    for _view in _info['gates']:
        VIEW_ADDON_MAP[_view] = _slug


def has_addon(user, slug):
    """Return True if *user* has an active purchase for the add-on *slug*."""
    if not user.is_authenticated or user.user_type != 'teacher':
        return False
    from teachers.models import TeacherAddOnPurchase
    return TeacherAddOnPurchase.objects.filter(
        teacher=user, addon__slug=slug, is_active=True,
    ).exists()


def get_purchased_slugs(user):
    """Return a set of active add-on slugs for the given teacher."""
    if not user.is_authenticated or user.user_type != 'teacher':
        return set()
    from teachers.models import TeacherAddOnPurchase
    return set(
        TeacherAddOnPurchase.objects.filter(
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
