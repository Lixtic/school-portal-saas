from django.utils import timezone
from django.db import transaction


def trial_status(request):
    """Inject trial subscription + AI quota info for the current tenant into every template."""
    if not hasattr(request, 'tenant') or not hasattr(request, 'user') or not request.user.is_authenticated:
        return {}

    # Use request-level cache set by TenantPathMiddleware.process_view() to avoid
    # a redundant DB query (middleware already fetched the subscription).
    # Sentinel: _tenant_subscription not set at all means middleware didn't run
    # (e.g. exempt path); None means it ran but no subscription exists.
    _sentinel = object()
    sub = getattr(request, '_tenant_subscription', _sentinel)
    if sub is _sentinel:
        # Middleware didn't cache it — fall back to DB
        from .models import SchoolSubscription
        try:
            with transaction.atomic():
                sub = SchoolSubscription.objects.select_related('plan').get(school=request.tenant)
        except SchoolSubscription.DoesNotExist:
            return {'trial_active': False}
        except Exception:
            return {}
    elif sub is None:
        return {'trial_active': False}

    ctx = {'trial_active': False, 'trial_subscription': sub}

    if sub.status == 'trial' and sub.trial_ends_at:
        days_left = max(0, (sub.trial_ends_at - timezone.now()).days)
        ctx.update({
            'trial_active': True,
            'trial_days_left': days_left,
            'trial_ends_at': sub.trial_ends_at,
        })

    # Grace period warning (set by middleware when trial expired but grace remains)
    if getattr(request, '_trial_grace_active', False):
        ctx['trial_grace_active'] = True
        ctx['trial_grace_days_left'] = getattr(request, '_trial_grace_days_left', 0)

    # Renewal warning for paid subscriptions nearing period end
    if sub.status == 'active' and sub.current_period_end:
        renew_days = max(0, (sub.current_period_end - timezone.now()).days)
        if renew_days <= 7:
            ctx['renewal_warning'] = True
            ctx['renewal_days_left'] = renew_days

    # AI quota summary — pass the already-fetched subscription to avoid extra DB query
    try:
        from .ai_quota import get_quota_status
        quota = get_quota_status(request.tenant, subscription=sub)
        ctx['ai_quota'] = quota
    except Exception:
        pass

    return ctx
