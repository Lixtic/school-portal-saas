"""Audit logging signals for finance events (Payment records)."""
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='finance.Payment')
def audit_payment_recorded(sender, instance, created, **kwargs):
    """Log payment creation to the platform audit trail."""
    if not created:
        return
    try:
        from tenants.subscription_models import AuditLog
        from django.db import connection
        import json

        student_fee = instance.student_fee
        student = student_fee.student
        detail = json.dumps({
            'student': student.user.get_full_name(),
            'student_id': student.pk,
            'amount': str(instance.amount),
            'reference': instance.reference or '',
            'method': getattr(instance, 'method', ''),
            'fee_status': student_fee.status,
        })
        AuditLog.objects.create(
            action='payment_recorded',
            user_id=student.user_id,
            username=student.user.username,
            tenant_schema=connection.schema_name,
            detail=detail,
        )
    except Exception:
        pass  # Never crash a save due to audit failure
