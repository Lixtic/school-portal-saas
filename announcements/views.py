from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Announcement, Notification, PushSubscription
from .forms import AnnouncementForm
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
from accounts.models import User
from django.db.utils import OperationalError, ProgrammingError, DatabaseError
import logging
import json

logger = logging.getLogger(__name__)


def _create_announcement_notifications(announcement):
    """Bulk-create Notification records for every user targeted by an announcement."""
    audience = announcement.target_audience
    qs = User.objects.exclude(pk=announcement.created_by_id)

    if audience == 'all':
        recipients = qs
    elif audience == 'staff':
        recipients = qs.filter(user_type__in=['admin', 'teacher'])
    elif audience == 'teachers':
        recipients = qs.filter(user_type='teacher')
    elif audience == 'students':
        recipients = qs.filter(user_type='student')
    elif audience == 'parents':
        recipients = qs.filter(user_type='parent')
    else:
        recipients = qs.none()

    # Remove any old notifications for this same announcement (e.g. on edit)
    Notification.objects.filter(announcement=announcement).delete()

    notifications = [
        Notification(
            recipient=user,
            message=f"📢 {announcement.title}",
            alert_type='announcement',
            announcement=announcement,
        )
        for user in recipients
    ]
    Notification.objects.bulk_create(notifications, ignore_conflicts=True)


@login_required
def announcement_list(request):
    """Public-facing announcement list for students, parents, and teachers."""
    user = request.user
    # Filter announcements based on user type
    if user.user_type == 'admin':
        return redirect('announcements:manage')
    
    audience_filters = Q(target_audience='all')
    if user.user_type == 'student':
        audience_filters |= Q(target_audience='students')
    elif user.user_type == 'parent':
        audience_filters |= Q(target_audience='parents')
    elif user.user_type == 'teacher':
        audience_filters |= Q(target_audience='teachers') | Q(target_audience='staff')
    
    announcements = Announcement.objects.filter(audience_filters, is_active=True).order_by('-created_at')
    
    return render(request, 'announcements/announcement_list.html', {
        'announcements': announcements,
    })


@login_required
def manage_announcements(request):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied')
        return redirect('dashboard')
        
    announcements = Announcement.objects.all()
    
    if request.method == 'POST':
        # Check if delete
        if 'delete' in request.POST:
            a_id = request.POST.get('delete')
            Announcement.objects.filter(id=a_id).delete()
            messages.success(request, 'Announcement deleted successfully.')
            return redirect('announcements:manage')
            
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.created_by = request.user
            announcement.save()
            _create_announcement_notifications(announcement)
            messages.success(request, 'Announcement posted successfully.')
            return redirect('announcements:manage')
            
    else:
        form = AnnouncementForm()
        
    return render(request, 'announcements/manage.html', {
        'announcements': announcements,
        'form': form
    })

@login_required
def notifications_unread_count(request):
    """Return the unread notification count + latest unread link as JSON (for client-side polling)."""
    try:
        qs = request.user.notifications.filter(is_read=False).order_by('-created_at')
        count = qs.count()
        latest = qs.values('link', 'message').first()
        latest_link = (latest.get('link') or '') if latest else ''
        return JsonResponse({'count': count, 'latest_link': latest_link})
    except (ProgrammingError, OperationalError, DatabaseError):
        # Tenant schema may not have announcements tables yet.
        logger.warning(
            "notifications_unread_count fallback: notifications table missing/unavailable for user=%s",
            getattr(request.user, 'id', None),
            exc_info=True,
        )
        return JsonResponse({'count': 0, 'latest_link': ''})


@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    # Route to contextually relevant page based on notification type
    if notification.alert_type == 'announcement':
        if request.user.user_type == 'admin':
            return redirect('announcements:manage')
        return redirect('announcements:list')
    if notification.alert_type == 'message' and notification.link:
        # link stores the sender's user pk — go straight to that thread
        try:
            return redirect('communication:conversation', user_id=int(notification.link))
        except (ValueError, TypeError):
            pass
        return redirect('communication:inbox')
    if notification.alert_type == 'message':
        return redirect('communication:inbox')
    # For all other types (general, fee, etc.) follow the stored link if present
    if notification.link:
        return redirect(notification.link)
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

@login_required
def mark_all_notifications_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


# ---------------------------------------------------------------------------
# Notification Centre
# ---------------------------------------------------------------------------

@login_required
def notification_centre(request):
    """Full inbox — all notifications for the logged-in user, newest first."""
    filter_tab = request.GET.get('tab', 'all')  # 'all' | 'unread'

    qs = Notification.objects.filter(recipient=request.user).order_by('-created_at')

    if filter_tab == 'unread':
        qs = qs.filter(is_read=False)

    # Mark all fetched notifications as read (passive auto-read)
    unread_ids = list(qs.filter(is_read=False).values_list('id', flat=True))
    if unread_ids:
        Notification.objects.filter(id__in=unread_ids).update(is_read=True)

    return render(request, 'announcements/notification_centre.html', {
        'notifications': qs,
        'active_tab': filter_tab,
        'unread_count_before': len(unread_ids),
    })


# ---------------------------------------------------------------------------
# PWA Push Subscriptions
# ---------------------------------------------------------------------------

@login_required
@require_POST
def push_subscribe(request):
    """Save / update a browser push subscription for the current user."""
    from django.conf import settings
    try:
        data = json.loads(request.body)
        endpoint = data.get('endpoint', '').strip()
        p256dh = data.get('keys', {}).get('p256dh', '').strip()
        auth_key = data.get('keys', {}).get('auth', '').strip()
    except (ValueError, KeyError):
        return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

    if not endpoint:
        return JsonResponse({'ok': False, 'error': 'Missing endpoint'}, status=400)

    PushSubscription.objects.update_or_create(
        endpoint=endpoint,
        defaults={'user': request.user, 'p256dh': p256dh, 'auth': auth_key},
    )
    return JsonResponse({'ok': True, 'public_key': settings.VAPID_PUBLIC_KEY})


@login_required
@require_http_methods(['POST', 'DELETE'])
def push_unsubscribe(request):
    """Remove a push subscription."""
    try:
        data = json.loads(request.body)
        endpoint = data.get('endpoint', '').strip()
    except (ValueError, KeyError):
        return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

    PushSubscription.objects.filter(user=request.user, endpoint=endpoint).delete()
    return JsonResponse({'ok': True})


def send_push_notification(user, title, body, url='/'):
    """
    Helper to send a web-push notification to all of a user's subscriptions.
    Call from signal handlers or management commands.
    """
    from django.conf import settings
    from pywebpush import webpush, WebPushException
    import json as _json

    subscriptions = PushSubscription.objects.filter(user=user)
    private_key_pem = settings.VAPID_PRIVATE_KEY_PEM
    claims = settings.VAPID_CLAIMS

    for sub in subscriptions:
        try:
            webpush(
                subscription_info={
                    'endpoint': sub.endpoint,
                    'keys': {'p256dh': sub.p256dh, 'auth': sub.auth},
                },
                data=_json.dumps({'title': title, 'body': body, 'url': url}),
                vapid_private_key=private_key_pem,
                vapid_claims=claims,
            )
        except WebPushException as ex:
            # Subscription expired — clean up
            if ex.response and ex.response.status_code in (404, 410):
                sub.delete()


# ── Offline Data API ────────────────────────────────────────────────────────

@login_required
def offline_announcements_json(request):
    """Return recent announcements as JSON for offline caching."""
    user = request.user
    user_type = getattr(user, 'user_type', 'student')

    qs = Announcement.objects.filter(is_active=True).order_by('-created_at')

    if user_type == 'admin':
        pass  # admins see all
    elif user_type in ('teacher',):
        qs = qs.filter(target_audience__in=['all', 'staff', 'teachers'])
    elif user_type == 'student':
        qs = qs.filter(target_audience__in=['all', 'students'])
    elif user_type == 'parent':
        qs = qs.filter(target_audience__in=['all', 'parents'])

    announcements = []
    for a in qs[:20]:
        announcements.append({
            'id': a.id,
            'title': a.title,
            'content': a.content[:500],
            'audience': a.target_audience,
            'created_at': a.created_at.isoformat() if a.created_at else '',
            'author': a.created_by.get_full_name() if a.created_by else '',
        })

    return JsonResponse({'announcements': announcements})
