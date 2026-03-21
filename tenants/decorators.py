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
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect


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
        if tenant is None or tenant.schema_name == 'public':
            return False

        from tenants.subscription_models import SchoolSubscription, SchoolAddOn
        # Use the request-level cache set by TenantPathMiddleware.process_view()
        # to avoid an extra DB round-trip per decorator call.
        _sentinel = object()
        subscription = getattr(request, '_tenant_subscription', _sentinel)
        if subscription is _sentinel:
            subscription = SchoolSubscription.objects.filter(school=tenant).first()
        if subscription is None:
            return False

        return SchoolAddOn.objects.filter(
            subscription=subscription,
            addon__slug=slug,
            is_active=True,
        ).exists()
    except Exception:
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
