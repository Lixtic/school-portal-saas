"""
AI usage quota enforcement for the SaaS platform.

Usage in views:
    from tenants.ai_quota import check_and_consume, QuotaExceeded, get_quota_status

    try:
        check_and_consume(request.tenant, request.user.id, 'lesson_gen')
    except QuotaExceeded as e:
        return JsonResponse({'status': 'error', 'error_code': 'quota_exceeded',
                             'message': e.user_message, 'used': e.used, 'limit': e.limit}, status=429)
"""
from django.db import transaction as _transaction
from django.db.utils import ProgrammingError as _ProgrammingError
from django.utils import timezone


# Default limits applied when a school has no subscription record
_DEFAULTS_BY_STATUS = {
    'no_subscription': 10,
}

# Human-readable action labels for error messages
_ACTION_LABELS = {
    'lesson_gen':     'lesson plan generation',
    'slide_gen':      'slide generation',
    'exercise_gen':   'exercise generation',
    'assignment_gen': 'assignment generation',
    'study_guide':    'study guide generation',
    'bulk_gen':       'bulk lesson generation',
    'other':          'AI generation',
}


class QuotaExceeded(Exception):
    def __init__(self, used, limit, action_type):
        self.used = used
        self.limit = limit
        self.action_type = action_type
        label = _ACTION_LABELS.get(action_type, 'AI generation')
        self.user_message = (
            f"Your school has reached its monthly AI quota ({used}/{limit} calls used). "
            f"Upgrade your plan to unlock more {label}."
        )
        super().__init__(self.user_message)


def _get_this_month_start():
    now = timezone.now()
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def get_quota_status(school, subscription=None):
    """
    Returns a dict with quota info for the school:
        {limit, used, remaining, unlimited, action_breakdown}
    Safe to call at any time — never raises.

    Pass ``subscription`` (a SchoolSubscription instance or None) to reuse an
    already-fetched subscription and avoid an extra DB round-trip.
    """
    limit = _DEFAULTS_BY_STATUS['no_subscription']
    unlimited = False

    try:
        with _transaction.atomic():
            if subscription is None:
                from .models import SchoolSubscription
                subscription = SchoolSubscription.objects.defer(
                    'paystack_subscription_code',
                    'paystack_customer_code',
                    'mrr',
                ).select_related('plan').get(school=school)
            if subscription is not None:
                limit = subscription.plan.ai_calls_per_month
    except Exception:
        pass

    if limit == -1:
        unlimited = True

    month_start = _get_this_month_start()
    used = 0
    breakdown = {}
    try:
        from .models import AIUsageLog
        with _transaction.atomic():
            qs = AIUsageLog.objects.filter(school=school, created_at__gte=month_start)
            used = qs.count()
            from django.db.models import Count
            breakdown = {
                row['action_type']: row['n']
                for row in qs.values('action_type').annotate(n=Count('id'))
            }
    except Exception:
        pass

    return {
        'limit': limit,
        'used': used,
        'remaining': None if unlimited else max(0, limit - used),
        'unlimited': unlimited,
        'action_breakdown': breakdown,
    }


def check_and_consume(school, user_id, action_type, call_count=1):
    """
    Check the school's AI quota and record usage.

    - If unlimited plan: logs and returns True.
    - If over quota: raises QuotaExceeded.
    - Otherwise: logs call_count entries and returns True.

    call_count > 1 is used for bulk operations.
    """
    from .models import SchoolSubscription, AIUsageLog

    limit = _DEFAULTS_BY_STATUS['no_subscription']

    try:
        sub = SchoolSubscription.objects.select_related('plan').get(school=school)
        limit = sub.plan.ai_calls_per_month
    except SchoolSubscription.DoesNotExist:
        pass
    except Exception:
        # Never hard-block on quota-check failure — just log
        _log_usage(school, user_id, action_type, call_count)
        return True

    if limit == -1:
        # Unlimited — just record
        _log_usage(school, user_id, action_type, call_count)
        return True

    if limit == 0:
        raise QuotaExceeded(0, 0, action_type)

    month_start = _get_this_month_start()
    used = AIUsageLog.objects.filter(school=school, created_at__gte=month_start).count()

    if used + call_count > limit:
        raise QuotaExceeded(used, limit, action_type)

    _log_usage(school, user_id, action_type, call_count)
    return True


def _log_usage(school, user_id, action_type, count=1):
    from .models import AIUsageLog
    AIUsageLog.objects.bulk_create([
        AIUsageLog(school=school, user_id=user_id, action_type=action_type)
        for _ in range(count)
    ])
