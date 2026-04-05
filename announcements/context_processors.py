from django.db.utils import OperationalError, ProgrammingError
from django.db import transaction

def user_notifications(request):
    if not hasattr(request, 'user') or request.user is None:
        return {}
    if request.user.is_authenticated:
        try:
            # Fetch one extra to detect "more than 5" without a separate COUNT query.
            with transaction.atomic():
                unread_plus = list(
                    request.user.notifications.filter(is_read=False).order_by('-created_at')[:6]
                )
            if len(unread_plus) < 6:
                # Fewer than 6 results means this IS the total; avoid a second DB round-trip.
                unread_count = len(unread_plus)
            else:
                # Could be more; exact count needed for the badge.
                with transaction.atomic():
                    unread_count = request.user.notifications.filter(is_read=False).count()
            return {
                'unread_notifications': unread_plus[:5],
                'unread_count': unread_count,
            }
        except Exception:
            # Catch ALL exceptions — OperationalError, ProgrammingError,
            # InterfaceError (stale connection), AttributeError, etc.
            # A context processor failure here would crash every page.
            return {'unread_notifications': [], 'unread_count': 0}
            
    return {}
