from django.utils import timezone


def trial_status(request):
    """Inject trial subscription + AI quota info for the current tenant into every template."""
    if not hasattr(request, 'tenant') or not request.user.is_authenticated:
        return {}

    from .models import SchoolSubscription
    try:
        sub = SchoolSubscription.objects.select_related('plan').get(school=request.tenant)
    except SchoolSubscription.DoesNotExist:
        return {'trial_active': False}
    except Exception:
        return {}

    ctx = {'trial_active': False, 'trial_subscription': sub}

    if sub.status == 'trial' and sub.trial_ends_at:
        days_left = max(0, (sub.trial_ends_at - timezone.now()).days)
        ctx.update({
            'trial_active': True,
            'trial_days_left': days_left,
            'trial_ends_at': sub.trial_ends_at,
        })

    # AI quota summary (inexpensive count query)
    try:
        from .ai_quota import get_quota_status
        quota = get_quota_status(request.tenant)
        ctx['ai_quota'] = quota
    except Exception:
        pass

    return ctx
