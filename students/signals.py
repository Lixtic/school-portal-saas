"""
students/signals.py
Parent notification signals:
  - Grade saved → notify parent(s)
  - Attendance saved (absent/late) → notify parent(s)
  - StudentFee status changed → notify parent(s)
"""
from django.db.models.signals import post_save
from django.dispatch import receiver


def _notify_parents(student, message, link='', alert_type='general'):
    """Create an announcements.Notification for every parent linked to student,
    and fire a push notification to each parent in a background thread."""
    try:
        from announcements.models import Notification
        from parents.models import Parent
        parents = Parent.objects.filter(children=student).select_related('user')
        parent_user_ids = []
        for parent in parents:
            Notification.objects.create(
                recipient=parent.user,
                message=message,
                link=link,
                alert_type=alert_type,
            )
            parent_user_ids.append(parent.user_id)
        # Fire push notifications in background thread
        if parent_user_ids:
            from announcements.views import send_push_to_users
            send_push_to_users(parent_user_ids, 'School Notification', message, link or '/')
    except Exception:
        pass  # Never crash a save due to notification failure


@receiver(post_save, sender='students.Grade')
def notify_parent_grade(sender, instance, created, **kwargs):
    if not created:
        return
    student = instance.student
    subject = getattr(instance, 'subject', None)
    subject_name = subject.name if subject else 'a subject'
    total = getattr(instance, 'total_score', None)
    score_str = f' — {total}/100' if total is not None else ''
    message = (
        f"New grade posted for {student.user.get_full_name()}: "
        f"{subject_name}{score_str} ({instance.term} term)"
    )
    _notify_parents(student, message, alert_type='general')


@receiver(post_save, sender='students.Grade')
def audit_grade_change(sender, instance, created, **kwargs):
    """Log grade creation/updates to the platform audit trail."""
    try:
        from tenants.subscription_models import AuditLog
        from django.db import connection
        import json
        student = instance.student
        detail = json.dumps({
            'student': student.user.get_full_name(),
            'student_id': student.pk,
            'subject': str(getattr(instance.subject, 'name', '')),
            'term': instance.term,
            'class_score': str(instance.class_score),
            'exams_score': str(instance.exams_score),
            'total': str(instance.total_score),
            'grade': instance.grade,
            'created': created,
        })
        AuditLog.objects.create(
            action='grade_change',
            user_id=student.user_id,
            username=student.user.username,
            tenant_schema=connection.schema_name,
            detail=detail,
        )
    except Exception:
        pass  # Never crash a save due to audit failure


@receiver(post_save, sender='students.Attendance')
def notify_parent_attendance(sender, instance, created, **kwargs):
    if not created:
        return
    if instance.status not in ('absent', 'late'):
        return
    student = instance.student
    status_display = instance.get_status_display() if hasattr(instance, 'get_status_display') else instance.status
    from datetime import date as _date
    _d = instance.date
    if isinstance(_d, str):
        try:
            from datetime import datetime as _dt
            _d = _dt.strptime(_d, '%Y-%m-%d').date()
        except Exception:
            _d = None
    date_str = _d.strftime('%b %d, %Y') if _d else str(instance.date)
    message = (
        f"{student.user.get_full_name()} was marked {status_display} "
        f"on {date_str}."
    )
    _notify_parents(student, message, alert_type='general')


@receiver(post_save, sender='finance.StudentFee')
def notify_parent_fee(sender, instance, created, **kwargs):
    if not created:
        return
    student = instance.student
    amount = getattr(instance, 'amount_payable', None)
    amount_str = f'₵{amount:,.2f}' if amount is not None else ''
    message = (
        f"A fee of {amount_str} has been assigned to {student.user.get_full_name()}."
    )
    _notify_parents(student, message, alert_type='general')
