from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages as django_messages
from django.http import JsonResponse
from django.db.models import Q, Count, Max, Subquery, OuterRef
from django.conf import settings
from django.utils import timezone

from accounts.models import User
from .models import Conversation, Message, SMSMessage, EmailCampaign, NotificationRule, NotificationRuleLog
from .forms import SMSForm, EmailForm
from students.models import Student
from teachers.models import Teacher
from announcements.models import Notification


def _notify_new_message(sender, recipient, preview):
    """Create a bell notification for the recipient of a new message.
    Suppressed if the recipient already has an unread notification from this
    sender to avoid spamming the bell on every reply in an active thread.
    """
    already = Notification.objects.filter(
        recipient=recipient,
        alert_type='message',
        link=str(sender.pk),
        is_read=False,
    ).exists()
    if already:
        return
    short = preview[:80] + ('…' if len(preview) > 80 else '')
    Notification.objects.create(
        recipient=recipient,
        message=f"💬 New message from {sender.get_full_name() or sender.username}: {short}",
        alert_type='message',
        link=str(sender.pk),  # store sender pk so we can redirect to the thread
    )


# ═══════════════════════════════
#  INBOX  – list all conversations
# ═══════════════════════════════

@login_required
def inbox(request):
    user = request.user
    convs = (
        Conversation.objects.filter(
            Q(participant1=user) | Q(participant2=user)
        )
        .select_related('participant1', 'participant2')
        .annotate(
            unread=Count(
                'messages',
                filter=Q(messages__is_read=False) & ~Q(messages__sender=user),
            ),
            latest_msg_time=Max('messages__created_at'),
        )
        .order_by('-updated_at')
    )

    # Prefetch the single latest message per conversation in one query
    from django.db.models import Prefetch
    latest_msg_qs = Message.objects.order_by('-created_at')
    convs = convs.prefetch_related(
        Prefetch('messages', queryset=latest_msg_qs, to_attr='_prefetched_msgs')
    )

    conversations = []
    for conv in convs:
        other = conv.other_participant(user)
        last_msg = conv._prefetched_msgs[0] if conv._prefetched_msgs else None
        conversations.append({
            'conv': conv,
            'other': other,
            'last_msg': last_msg,
            'unread': conv.unread,
        })

    context = {
        'conversations': conversations,
        'total_unread': sum(c['unread'] for c in conversations),
    }
    return render(request, 'communication/inbox.html', context)


# ═══════════════════════════════
#  CONVERSATION – read + reply
# ═══════════════════════════════

@login_required
def conversation_view(request, user_id):
    other_user = get_object_or_404(User, pk=user_id)

    if other_user == request.user:
        return redirect('communication:inbox')

    # Enforce role-based messaging rules
    allowed_ids = set(_allowed_recipients(request.user).values_list('pk', flat=True))
    if other_user.pk not in allowed_ids:
        django_messages.error(request, 'You are not allowed to message this person.')
        return redirect('communication:inbox')

    conv, _ = Conversation.get_or_create_between(request.user, other_user)

    # Mark messages from the other person as read
    conv.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    # Also clear the bell notification for messages from this sender
    Notification.objects.filter(
        recipient=request.user,
        alert_type='message',
        link=str(other_user.pk),
        is_read=False,
    ).update(is_read=True)

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Message.objects.create(
                conversation=conv,
                sender=request.user,
                content=content,
            )
            conv.save()  # bumps updated_at
            _notify_new_message(request.user, other_user, content)
        return redirect('communication:conversation', user_id=user_id)

    messages_qs = conv.messages.select_related('sender').order_by('created_at')

    context = {
        'conv': conv,
        'other_user': other_user,
        'messages': messages_qs,
    }
    return render(request, 'communication/conversation.html', context)


# ═══════════════════════════════
#  COMPOSE – start a new thread
# ═══════════════════════════════

@login_required
def compose(request):
    user = request.user

    if request.method == 'POST':
        recipient_id = request.POST.get('recipient_id')
        content = request.POST.get('content', '').strip()
        if not recipient_id or not content:
            django_messages.error(request, 'Please select a recipient and write a message.')
            return redirect('communication:compose')

        other_user = get_object_or_404(User, pk=recipient_id)
        # Enforce role-based messaging rules
        allowed_ids = set(_allowed_recipients(user).values_list('pk', flat=True))
        if other_user.pk not in allowed_ids:
            django_messages.error(request, 'You are not allowed to message this person.')
            return redirect('communication:compose')
        conv, _ = Conversation.get_or_create_between(user, other_user)
        Message.objects.create(conversation=conv, sender=user, content=content)
        conv.save()
        _notify_new_message(user, other_user, content)
        return redirect('communication:conversation', user_id=other_user.pk)

    recipients = _allowed_recipients(user)
    context = {'recipients': recipients}
    return render(request, 'communication/compose.html', context)


def _allowed_recipients(user):
    """Return users this person is allowed to message, based on their role."""
    qs = User.objects.exclude(pk=user.pk)

    if user.user_type == 'admin':
        return qs.order_by('user_type', 'last_name', 'first_name')

    elif user.user_type == 'teacher':
        teacher = Teacher.objects.filter(user=user).first()
        allowed_ids = set(User.objects.filter(user_type='admin').values_list('pk', flat=True))
        allowed_ids.update(User.objects.filter(user_type='teacher').values_list('pk', flat=True))
        if teacher:
            student_ids = Student.objects.filter(
                current_class__classsubject__teacher=teacher
            ).values_list('user_id', flat=True)
            allowed_ids.update(student_ids)
            from parents.models import Parent
            parent_ids = Parent.objects.filter(
                children__current_class__classsubject__teacher=teacher
            ).values_list('user_id', flat=True)
            allowed_ids.update(parent_ids)
        return qs.filter(pk__in=allowed_ids).order_by('user_type', 'last_name', 'first_name')

    elif user.user_type == 'student':
        allowed_ids = set(User.objects.filter(user_type='admin').values_list('pk', flat=True))
        student = Student.objects.filter(user=user).first()
        if student and student.current_class:
            teacher_ids = Teacher.objects.filter(
                classsubject__class_name=student.current_class
            ).values_list('user_id', flat=True)
            allowed_ids.update(teacher_ids)
        return qs.filter(pk__in=allowed_ids).order_by('user_type', 'last_name', 'first_name')

    elif user.user_type == 'parent':
        from parents.models import Parent
        allowed_ids = set(User.objects.filter(user_type='admin').values_list('pk', flat=True))
        parent = Parent.objects.filter(user=user).first()
        if parent:
            teacher_ids = Teacher.objects.filter(
                classsubject__class_name__student__in=parent.children.all()
            ).values_list('user_id', flat=True)
            allowed_ids.update(teacher_ids)
        return qs.filter(pk__in=allowed_ids).order_by('user_type', 'last_name', 'first_name')

    return qs.none()


# ═══════════════════════════════
#  API – unread count badge
# ═══════════════════════════════

@login_required
def api_unread_count(request):
    try:
        user = request.user
        count = Message.objects.filter(
            conversation__in=Conversation.for_user(user),
            is_read=False,
        ).exclude(sender=user).count()
        return JsonResponse({'unread': count})
    except Exception:
        return JsonResponse({'unread': 0})


# ═══════════════════════════════
#  BROADCAST (admin only)
# ═══════════════════════════════

@login_required
def broadcast_dashboard(request):
    if request.user.user_type != 'admin':
        return redirect('communication:inbox')

    recent_sms = SMSMessage.objects.order_by('-created_at')[:8]
    recent_emails = EmailCampaign.objects.order_by('-created_at')[:8]

    return render(request, 'communication/broadcast_dashboard.html', {
        'recent_sms': recent_sms,
        'recent_emails': recent_emails,
    })


@login_required
def send_sms(request):
    if request.user.user_type != 'admin':
        django_messages.error(request, "Access Denied")
        return redirect('dashboard')

    if request.method == 'POST':
        form = SMSForm(request.POST)
        if form.is_valid():
            recipient_type = form.cleaned_data['recipient_type']
            target_class = form.cleaned_data['target_class']
            message_body = form.cleaned_data['message_body']
            recipients = set()
            try:
                if recipient_type == 'individual':
                    number = form.cleaned_data.get('recipient_number')
                    if number:
                        recipients.add(number)
                elif recipient_type == 'class':
                    if target_class:
                        for s in Student.objects.filter(current_class=target_class).prefetch_related('parents__user'):
                            for p in s.parents.all():
                                if p.user.phone:
                                    recipients.add(p.user.phone)
                    else:
                        django_messages.error(request, "Please select a class")
                        return render(request, 'communication/send_sms.html', {'form': form})
                elif recipient_type == 'teachers':
                    for t in Teacher.objects.select_related('user'):
                        if t.user.phone:
                            recipients.add(t.user.phone)
                elif recipient_type == 'staff':
                    for u in User.objects.filter(user_type__in=['admin', 'teacher']):
                        if u.phone:
                            recipients.add(u.phone)

                if not recipients:
                    django_messages.warning(request, "No valid phone numbers found.")
                    return redirect('communication:send_sms')

                from announcements.sms_service import send_sms as at_send_sms
                import logging
                _log = logging.getLogger(__name__)

                sent_count = 0
                failed_count = 0
                phone_list = list(recipients)

                # Send in batches of 20 to avoid API limits
                for i in range(0, len(phone_list), 20):
                    batch = phone_list[i:i + 20]
                    result = at_send_sms(batch, message_body)
                    if result.get('error'):
                        # API not configured — fall back to recording as queued
                        for phone in batch:
                            SMSMessage.objects.create(
                                recipient_number=phone,
                                message_body=message_body,
                                status='queued',
                                provider_response=result['error'],
                                sent_by=request.user,
                            )
                        failed_count += len(batch)
                    else:
                        for phone in batch:
                            SMSMessage.objects.create(
                                recipient_number=phone,
                                message_body=message_body,
                                status='sent',
                                provider_response=str(result),
                                sent_at=timezone.now(),
                                sent_by=request.user,
                            )
                        sent_count += len(batch)

                if failed_count and not sent_count:
                    django_messages.warning(request, f"SMS gateway unavailable. {failed_count} message(s) queued for retry.")
                elif failed_count:
                    django_messages.warning(request, f"Sent {sent_count}, failed {failed_count} SMS message(s).")
                else:
                    django_messages.success(request, f"SMS sent to {sent_count} recipient(s).")
                return redirect('communication:broadcast_dashboard')
            except Exception as e:
                django_messages.error(request, f"Error: {str(e)}")
    else:
        form = SMSForm()

    return render(request, 'communication/send_sms.html', {'form': form})


@login_required
def send_email(request):
    if request.user.user_type != 'admin':
        return redirect('dashboard')

    if request.method == 'POST':
        form = EmailForm(request.POST)
        if form.is_valid():
            campaign = form.save(commit=False)
            campaign.sent_by = request.user
            campaign.save()

            # Resolve recipient emails based on group
            from django.core.mail import send_mass_mail
            import logging
            _log = logging.getLogger(__name__)

            email_list = []
            group = campaign.recipient_group
            if group == 'staff':
                email_list = list(
                    User.objects.filter(user_type__in=['admin', 'teacher'])
                    .exclude(email='')
                    .values_list('email', flat=True)
                )
            elif group == 'parents':
                email_list = list(
                    User.objects.filter(user_type='parent')
                    .exclude(email='')
                    .values_list('email', flat=True)
                )
            elif group == 'students':
                email_list = list(
                    User.objects.filter(user_type='student')
                    .exclude(email='')
                    .values_list('email', flat=True)
                )

            if email_list:
                from_addr = settings.DEFAULT_FROM_EMAIL
                messages_to_send = [
                    (campaign.subject, campaign.body, from_addr, [addr])
                    for addr in email_list
                ]
                try:
                    send_mass_mail(messages_to_send, fail_silently=False)
                    campaign.status = 'sent'
                    campaign.save(update_fields=['status'])
                    django_messages.success(request, f"Email sent to {len(email_list)} recipient(s).")
                except Exception as exc:
                    _log.exception('Email campaign send failed')
                    campaign.status = 'draft'
                    campaign.save(update_fields=['status'])
                    django_messages.warning(request, f"Email sending failed: {exc}. Campaign saved as draft.")
            else:
                campaign.status = 'sent'
                campaign.save(update_fields=['status'])
                django_messages.warning(request, "No email addresses found for the selected group.")

            return redirect('communication:broadcast_dashboard')
    else:
        form = EmailForm()

    return render(request, 'communication/send_email.html', {'form': form})


# ──────────────────────────────────────────────
# AUTO PARENT NOTIFICATION RULES
# ──────────────────────────────────────────────

import json
import logging
import datetime
from decimal import Decimal
from django.db.models import Avg, Count, Sum
from django.views.decorators.http import require_POST

_logger = logging.getLogger(__name__)


@login_required
def notification_rules(request):
    """List all notification rules — admin only."""
    if request.user.user_type != 'admin':
        django_messages.error(request, 'Access denied')
        return redirect('dashboard')

    rules = NotificationRule.objects.all()
    recent_logs = NotificationRuleLog.objects.select_related(
        'rule', 'student', 'student__user',
    ).order_by('-sent_at')[:30]

    return render(request, 'communication/notification_rules.html', {
        'rules': rules,
        'recent_logs': recent_logs,
        'trigger_choices': NotificationRule.TRIGGER_CHOICES,
        'channel_choices': NotificationRule.CHANNEL_CHOICES,
    })


@login_required
def notification_rule_save(request):
    """Create or update a notification rule (JSON)."""
    if request.user.user_type != 'admin':
        return JsonResponse({'error': 'Access denied'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    name = (data.get('name') or '').strip()
    if not name:
        return JsonResponse({'error': 'Name is required'}, status=400)

    trigger = data.get('trigger', '')
    if trigger not in dict(NotificationRule.TRIGGER_CHOICES):
        return JsonResponse({'error': 'Invalid trigger type'}, status=400)

    try:
        threshold = Decimal(str(data.get('threshold', 0)))
    except Exception:
        return JsonResponse({'error': 'Invalid threshold'}, status=400)

    channel = data.get('channel', 'in_app')
    if channel not in dict(NotificationRule.CHANNEL_CHOICES):
        channel = 'in_app'

    try:
        cooldown = int(data.get('cooldown_hours', 24))
    except (ValueError, TypeError):
        cooldown = 24

    rule_id = data.get('id')
    if rule_id:
        rule = get_object_or_404(NotificationRule, id=rule_id)
    else:
        rule = NotificationRule(created_by=request.user)

    rule.name = name
    rule.trigger = trigger
    rule.threshold = threshold
    rule.channel = channel
    rule.cooldown_hours = max(1, cooldown)
    rule.is_active = data.get('is_active', True)
    rule.save()

    return JsonResponse({'ok': True, 'id': rule.id})


@login_required
@require_POST
def notification_rule_delete(request, pk):
    """Delete a notification rule."""
    if request.user.user_type != 'admin':
        return JsonResponse({'error': 'Access denied'}, status=403)
    rule = get_object_or_404(NotificationRule, id=pk)
    rule.delete()
    return JsonResponse({'ok': True})


@login_required
@require_POST
def notification_rule_toggle(request, pk):
    """Toggle a rule's is_active flag."""
    if request.user.user_type != 'admin':
        return JsonResponse({'error': 'Access denied'}, status=403)
    rule = get_object_or_404(NotificationRule, id=pk)
    rule.is_active = not rule.is_active
    rule.save(update_fields=['is_active'])
    return JsonResponse({'ok': True, 'is_active': rule.is_active})


@login_required
@require_POST
def evaluate_notification_rules(request):
    """
    Manually trigger evaluation of all active rules.
    Finds students matching each rule, sends notifications respecting cooldown.
    Returns JSON summary.
    """
    if request.user.user_type != 'admin':
        return JsonResponse({'error': 'Access denied'}, status=403)

    rules = NotificationRule.objects.filter(is_active=True)
    summary = []

    for rule in rules:
        result = _evaluate_single_rule(rule)
        summary.append({
            'rule': rule.name,
            'trigger': rule.get_trigger_display(),
            'students_matched': result['matched'],
            'notifications_sent': result['sent'],
        })

    return JsonResponse({'ok': True, 'results': summary})


def _evaluate_single_rule(rule):
    """Evaluate one rule and send notifications. Returns counts."""
    from academics.models import AcademicYear
    from students.models import Attendance, Grade
    from finance.models import StudentFee
    from parents.models import Parent

    now = timezone.now()
    cooldown_cutoff = now - datetime.timedelta(hours=rule.cooldown_hours)
    threshold = float(rule.threshold)

    matched_students = []

    if rule.trigger == 'attendance_below':
        # Students whose attendance % < threshold
        current_year = AcademicYear.objects.filter(is_current=True).first()
        att_stats = Attendance.objects.all()
        if current_year:
            att_stats = att_stats.filter(date__gte=current_year.start_date)

        stats = att_stats.values('student_id').annotate(
            total=Count('id'),
            present=Count('id', filter=Q(status='present')),
        )
        for row in stats:
            if row['total'] > 0:
                pct = (row['present'] / row['total']) * 100
                if pct < threshold:
                    matched_students.append((row['student_id'], f"Attendance at {pct:.1f}% (below {threshold:.0f}%)"))

    elif rule.trigger == 'grade_below':
        current_year = AcademicYear.objects.filter(is_current=True).first()
        grades_qs = Grade.objects.all()
        if current_year:
            grades_qs = grades_qs.filter(academic_year=current_year)

        avgs = grades_qs.values('student_id').annotate(avg=Avg('total_score'))
        for row in avgs:
            if row['avg'] is not None and float(row['avg']) < threshold:
                matched_students.append((row['student_id'], f"Average grade {float(row['avg']):.1f}% (below {threshold:.0f}%)"))

    elif rule.trigger == 'fee_overdue':
        days_threshold = int(threshold)
        cutoff_date = now.date() - datetime.timedelta(days=days_threshold)
        overdue = StudentFee.objects.filter(
            status__in=['unpaid', 'partial'],
            fee_structure__due_date__isnull=False,
            fee_structure__due_date__lte=cutoff_date,
        ).select_related('student', 'fee_structure', 'fee_structure__head')

        for fee in overdue:
            msg = f"Fee '{fee.fee_structure.head.name}' overdue by {(now.date() - fee.fee_structure.due_date).days} days (balance: GHS {fee.balance:.2f})"
            matched_students.append((fee.student_id, msg))

    elif rule.trigger == 'absent_streak':
        streak_threshold = int(threshold)
        today = now.date()
        # Check recent attendance for consecutive absences
        students_with_att = Attendance.objects.filter(
            status='absent',
        ).values('student_id').annotate(
            absent_count=Count('id'),
        ).filter(absent_count__gte=1)

        for row in students_with_att:
            # Get last N days of attendance for this student
            recent = list(Attendance.objects.filter(
                student_id=row['student_id'],
            ).order_by('-date').values_list('status', flat=True)[:streak_threshold + 2])

            # Count consecutive absences from most recent
            streak = 0
            for status in recent:
                if status == 'absent':
                    streak += 1
                else:
                    break

            if streak >= streak_threshold:
                matched_students.append((row['student_id'], f"Absent {streak} consecutive days (threshold: {streak_threshold})"))

    # Deduplicate by student_id (keep first message)
    seen = set()
    unique = []
    for sid, msg in matched_students:
        if sid not in seen:
            seen.add(sid)
            unique.append((sid, msg))
    matched_students = unique

    # Send notifications, respecting cooldown
    sent_count = 0
    student_ids = [sid for sid, _ in matched_students]
    if not student_ids:
        return {'matched': 0, 'sent': 0}

    students = Student.objects.select_related('user', 'current_class').filter(id__in=student_ids)
    student_map = {s.id: s for s in students}

    # Get parents for these students
    from parents.models import Parent
    parent_links = Parent.objects.filter(
        children__id__in=student_ids,
    ).select_related('user').prefetch_related('children')

    student_parents = {}  # student_id -> [parent_user, ...]
    for parent in parent_links:
        for child in parent.children.all():
            if child.id in seen:
                student_parents.setdefault(child.id, []).append(parent.user)

    # Check cooldown
    recent_logs = NotificationRuleLog.objects.filter(
        rule=rule,
        sent_at__gte=cooldown_cutoff,
    ).values_list('student_id', flat=True)
    cooled_students = set(recent_logs)

    for sid, message in matched_students:
        if sid in cooled_students:
            continue
        student = student_map.get(sid)
        if not student:
            continue

        parent_users = student_parents.get(sid, [])
        if not parent_users:
            # Fallback: try emergency contact for SMS
            if rule.channel in ('sms', 'all'):
                _send_emergency_sms(student, rule, message)
            continue

        for parent_user in parent_users:
            _dispatch_notification(rule, student, parent_user, message)
            NotificationRuleLog.objects.create(
                rule=rule,
                student=student,
                parent=parent_user,
                channel=rule.channel,
                message=message,
            )
            sent_count += 1

    return {'matched': len(matched_students), 'sent': sent_count}


def _dispatch_notification(rule, student, parent_user, message):
    """Send via the configured channel(s)."""
    student_name = student.user.get_full_name()
    full_msg = f"[{rule.name}] {student_name}: {message}"

    channels = [rule.channel] if rule.channel != 'all' else ['in_app', 'email', 'sms']

    for ch in channels:
        try:
            if ch == 'in_app':
                Notification.objects.create(
                    recipient=parent_user,
                    message=full_msg[:255],
                    alert_type='general',
                )
            elif ch == 'email' and parent_user.email:
                from django.core.mail import send_mail
                send_mail(
                    subject=f"SchoolPadi Alert: {rule.name}",
                    message=full_msg,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[parent_user.email],
                    fail_silently=True,
                )
            elif ch == 'sms' and parent_user.phone:
                from announcements.sms_service import send_sms as at_send_sms
                phone = parent_user.phone.strip()
                if phone.startswith('0') and len(phone) == 10:
                    phone = '+233' + phone[1:]
                elif not phone.startswith('+'):
                    phone = '+' + phone
                at_send_sms([phone], full_msg)
        except Exception as exc:
            _logger.exception('Notification dispatch failed (%s): %s', ch, exc)


def _send_emergency_sms(student, rule, message):
    """Fallback: send SMS to student emergency_contact if no parent user found."""
    phone = getattr(student, 'emergency_contact', '').strip()
    if not phone:
        return
    if phone.startswith('0') and len(phone) == 10:
        phone = '+233' + phone[1:]
    elif not phone.startswith('+'):
        phone = '+' + phone

    full_msg = f"[{rule.name}] {student.user.get_full_name()}: {message}"
    try:
        from announcements.sms_service import send_sms as at_send_sms
        at_send_sms([phone], full_msg)
    except Exception as exc:
        _logger.exception('Emergency SMS failed: %s', exc)
