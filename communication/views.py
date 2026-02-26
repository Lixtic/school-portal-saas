from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages as django_messages
from django.http import JsonResponse
from django.db.models import Q

from accounts.models import User
from .models import Conversation, Message, SMSMessage, EmailCampaign
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
    convs = Conversation.for_user(user)

    conversations = []
    for conv in convs:
        other = conv.other_participant(user)
        last_msg = conv.last_message()
        unread = conv.unread_count_for(user)
        conversations.append({
            'conv': conv,
            'other': other,
            'last_msg': last_msg,
            'unread': unread,
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
    user = request.user
    count = Message.objects.filter(
        conversation__in=Conversation.for_user(user),
        is_read=False,
    ).exclude(sender=user).count()
    return JsonResponse({'unread': count})


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

                for phone in recipients:
                    SMSMessage.objects.create(
                        recipient_number=phone,
                        message_body=message_body,
                        status='sent',
                        provider_response='Mock Gateway: Delivered',
                        sent_by=request.user,
                    )
                django_messages.success(request, f"SMS sent to {len(recipients)} recipient(s).")
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
            email = form.save(commit=False)
            email.sent_by = request.user
            email.status = 'sent'
            email.save()
            django_messages.success(request, "Email campaign queued successfully.")
            return redirect('communication:broadcast_dashboard')
    else:
        form = EmailForm()

    return render(request, 'communication/send_email.html', {'form': form})
