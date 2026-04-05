"""
Add-on gating decorators for school tenant views.

Usage:
    from tenants.decorators import require_addon

    @login_required
    @require_addon('ai-admissions-assistant')
    def my_view(request):
        ...

If the school's active subscription doesn't include the requested add-on slug,
the user is redirected to the add-on marketplace with an informative message.
For JSON/AJAX endpoints, a 402 JSON response is returned instead.
"""

import functools
import logging
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect

logger = logging.getLogger(__name__)


def _school_has_addon(request, slug):
    """
    Return True if the current tenant's active subscription includes the add-on
    identified by *slug*.  Staff/superusers always get access (dev convenience).
    Returns False on any DB/config error so we degrade gracefully.
    """
    if request.user.is_staff or request.user.is_superuser:
        return True

    try:
        tenant = getattr(request, 'tenant', None)
        if tenant is None:
            return False
        if tenant.schema_name == 'public':
            return True  # Public landing page features are always available

        from tenants.subscription_models import SchoolSubscription, SchoolAddOn
        from django.db.models import Q
        from django.utils import timezone
        # Use the request-level cache set by TenantPathMiddleware.process_view()
        # to avoid an extra DB round-trip per decorator call.
        _sentinel = object()
        subscription = getattr(request, '_tenant_subscription', _sentinel)
        if subscription is _sentinel:
            subscription = SchoolSubscription.objects.filter(school=tenant).first()
        if subscription is None:
            return False

        now = timezone.now()
        return SchoolAddOn.objects.filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now),
            subscription=subscription,
            addon__slug=slug,
            is_active=True,
        ).exists()
    except Exception as exc:
        logger.debug("Addon check for '%s' failed: %s", slug, exc)
        return False


def require_addon(slug):
    """
    Decorator factory.  Wrap a view with ``@require_addon('my-addon-slug')``.

    * Regular requests  → redirect to the add-on marketplace with a message.
    * JSON/AJAX requests → 402 JSON response.
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not _school_has_addon(request, slug):
                # Detect AJAX / JSON requests by Accept or Content-Type header
                is_json = (
                    request.headers.get('Accept', '').startswith('application/json')
                    or request.content_type == 'application/json'
                    or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                )
                if is_json:
                    return JsonResponse(
                        {
                            'error': 'add_on_required',
                            'slug': slug,
                            'message': (
                                'This feature requires the add-on to be active. '
                                'Purchase it from the Marketplace to unlock it.'
                            ),
                        },
                        status=402,
                    )

                try:
                    from tenants.subscription_models import AddOn
                    addon_name = AddOn.objects.filter(slug=slug).values_list('name', flat=True).first() or slug
                except Exception:
                    addon_name = slug

                messages.warning(
                    request,
                    f'"{addon_name}" is a premium add-on. '
                    f'Purchase it from the Marketplace to unlock this feature.',
                )
                return redirect('tenants:addon_marketplace')

            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# Plan-level gating
# ---------------------------------------------------------------------------

def _school_plan_type(request):
    """
    Return the current tenant's active plan_type string (e.g. 'basic', 'pro',
    'enterprise', 'trial'), or None when it cannot be determined.
    Staff / superusers always bypass plan checks.
    """
    if request.user.is_staff or request.user.is_superuser:
        return 'enterprise'  # unrestricted for staff

    try:
        tenant = getattr(request, 'tenant', None)
        if tenant is None or tenant.schema_name == 'public':
            return None

        from tenants.subscription_models import SchoolSubscription
        _sentinel = object()
        subscription = getattr(request, '_tenant_subscription', _sentinel)
        if subscription is _sentinel:
            subscription = SchoolSubscription.objects.select_related('plan').filter(school=tenant).first()
        if subscription is None:
            return None
        if subscription.status not in ('trial', 'active'):
            return None  # treat suspended / past_due / cancelled as no access
        return subscription.plan.plan_type
    except Exception as exc:
        logger.debug("Plan check failed: %s", exc)
        return None


def require_plan(*plan_types):
    """
    View decorator — only allow access when the school's active plan is one of
    the given plan_types.

    Usage::

        @login_required
        @require_plan('basic', 'pro', 'enterprise')
        def premium_view(request):
            ...

        @login_required
        @require_plan('pro', 'enterprise')
        def advanced_view(request):
            ...

    * Trial schools are blocked unless 'trial' is in plan_types.
    * Staff / superusers always pass through.
    * AJAX / JSON → 402 response.
    * Normal requests → redirect to upgrade page with a message.
    """
    allowed = set(plan_types)

    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            current_plan = _school_plan_type(request)
            # Staff bypass: _school_plan_type returns 'enterprise' for staff
            if current_plan not in allowed:
                is_json = (
                    request.headers.get('Accept', '').startswith('application/json')
                    or request.content_type == 'application/json'
                    or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                )
                if is_json:
                    return JsonResponse(
                        {
                            'error': 'plan_upgrade_required',
                            'required_plans': list(allowed),
                            'current_plan': current_plan,
                            'message': (
                                'Your current plan does not include this feature. '
                                'Upgrade your subscription to unlock it.'
                            ),
                        },
                        status=402,
                    )

                plan_display = ' or '.join(p.title() for p in sorted(allowed - {'trial'}))
                messages.warning(
                    request,
                    f'This feature requires a {plan_display} plan. '
                    f'Upgrade your subscription to unlock it.',
                )
                # Redirect to subscription / billing page; fall back to dashboard
                try:
                    from django.urls import reverse
                    return redirect(reverse('tenants:addon_marketplace'))
                except Exception:
                    return redirect('/')

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
