from django.utils import timezone


def trial_status(request):
    """Inject trial subscription info for the current tenant into every template."""
    if not hasattr(request, 'tenant') or not request.user.is_authenticated:
        return {}

    from .models import SchoolSubscription
    try:
        sub = SchoolSubscription.objects.select_related('plan').get(school=request.tenant)
    except SchoolSubscription.DoesNotExist:
        return {'trial_active': False}
    except Exception:
        return {}

    if sub.status == 'trial' and sub.trial_ends_at:
        days_left = max(0, (sub.trial_ends_at - timezone.now()).days)
        return {
            'trial_active': True,
            'trial_days_left': days_left,
            'trial_ends_at': sub.trial_ends_at,
            'trial_subscription': sub,
        }

    return {'trial_active': False, 'trial_subscription': sub}
