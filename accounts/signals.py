"""Audit logging signals for authentication events."""
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver


@receiver(user_logged_in)
def audit_login(sender, request, user, **kwargs):
    from tenants.subscription_models import AuditLog
    AuditLog.log('login', request=request, user=user)


@receiver(user_logged_out)
def audit_logout(sender, request, user, **kwargs):
    from tenants.subscription_models import AuditLog
    AuditLog.log('logout', request=request, user=user)


@receiver(user_login_failed)
def audit_login_failed(sender, credentials, request, **kwargs):
    from tenants.subscription_models import AuditLog
    uname = credentials.get('username', '???')
    AuditLog.log('login_failed', request=request, detail=f'username={uname}')
