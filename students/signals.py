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
    """Create an announcements.Notification for every parent linked to student."""
    try:
        from announcements.models import Notification
        from parents.models import Parent
        parents = Parent.objects.filter(children=student).select_related('user')
        for parent in parents:
            Notification.objects.create(
                recipient=parent.user,
                message=message,
                link=link,
                alert_type=alert_type,
            )
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
