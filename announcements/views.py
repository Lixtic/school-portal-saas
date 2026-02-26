from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Announcement, Notification
from .forms import AnnouncementForm
from django.db.models import Q
from accounts.models import User


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
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

@login_required
def mark_all_notifications_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

