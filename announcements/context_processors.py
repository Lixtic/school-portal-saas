from django.db.utils import OperationalError, ProgrammingError

def user_notifications(request):
    if request.user.is_authenticated:
        try:
            # Force evaluation (list()) so DB errors are caught here,
            # not later in the template when the queryset is iterated.
            return {
                'unread_notifications': list(request.user.notifications.filter(is_read=False).order_by('-created_at')[:5]),
                'unread_count': request.user.notifications.filter(is_read=False).count()
            }
        except Exception:
            # Catch ALL exceptions — OperationalError, ProgrammingError,
            # InterfaceError (stale connection), AttributeError, etc.
            # A context processor failure here would crash every page.
            return {'unread_notifications': [], 'unread_count': 0}
            
    return {}
