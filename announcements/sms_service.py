"""
SMS utility for Portals.
Uses Africa's Talking as the SMS gateway.

Required env vars (set in .env or Vercel / Railway dashboard):
  AT_USERNAME  — your Africa's Talking username (use 'sandbox' for testing)
  AT_API_KEY   — your Africa's Talking API key

Install the SDK:
  pip install africastalking
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def send_sms(recipients: list[str], message: str, sender_id: str = '') -> dict:
    """
    Send an SMS message to one or more phone numbers via Africa's Talking.

    Args:
        recipients: List of E.164-formatted phone numbers, e.g. ['+233201234567']
        message:    The text to send (max ~160 chars per SMS segment)
        sender_id:  Optional alphanumeric sender ID (leave blank to use AT default)

    Returns:
        A dict summarising the API response, or an error dict on failure.

    Usage::

        from announcements.sms_service import send_sms
        result = send_sms(['+233201234567'], 'Hello from Portals!')
    """
    username = getattr(settings, 'AFRICASTALKING_USERNAME', 'sandbox')
    api_key  = getattr(settings, 'AFRICASTALKING_API_KEY',  '')

    if not api_key:
        logger.warning('SMS not sent — AFRICASTALKING_API_KEY is not configured.')
        return {'error': 'AFRICASTALKING_API_KEY not set', 'sent': 0}

    if not recipients:
        return {'error': 'No recipients', 'sent': 0}

    try:
        import africastalking  # noqa: F401 — optional dependency
    except ImportError:
        logger.error(
            'africastalking package is not installed. '
            'Run: pip install africastalking'
        )
        return {'error': 'africastalking package not installed', 'sent': 0}

    try:
        africastalking.initialize(username, api_key)
        sms = africastalking.SMS

        kwargs = dict(
            message=message,
            recipients=recipients,
        )
        if sender_id:
            kwargs['senderId'] = sender_id

        response = sms.send(**kwargs)
        logger.info('SMS sent to %d recipients. Response: %s', len(recipients), response)
        return {'sent': len(recipients), 'response': response}

    except Exception as exc:
        logger.exception('SMS sending failed: %s', exc)
        return {'error': str(exc), 'sent': 0}


def send_attendance_alert(student, status: str, date_str: str) -> dict:
    """
    Send an attendance SMS to the student's emergency contact.

    Args:
        student:   Student model instance
        status:    'present' | 'absent' | 'late'
        date_str:  Date string, e.g. '2025-01-15'
    """
    phone = getattr(student, 'emergency_contact', '').strip()
    if not phone:
        return {'error': 'No emergency contact for student', 'sent': 0}

    # Normalise to E.164 (basic attempt for GH numbers)
    if phone.startswith('0') and len(phone) == 10:
        phone = '+233' + phone[1:]
    elif not phone.startswith('+'):
        phone = '+' + phone

    name     = student.user.get_full_name()
    cls_name = student.current_class.name if student.current_class else 'their class'
    status_lbl = status.capitalize()

    if status == 'absent':
        msg = (
            f"ATTENDANCE ALERT: {name} was marked ABSENT from {cls_name} "
            f"on {date_str}. Please contact the school if this is unexpected."
        )
    elif status == 'late':
        msg = (
            f"ATTENDANCE ALERT: {name} arrived LATE to {cls_name} "
            f"on {date_str}."
        )
    else:
        msg = (
            f"ATTENDANCE: {name} was marked PRESENT in {cls_name} "
            f"on {date_str}."
        )

    return send_sms([phone], msg)


def send_fee_sms_reminder(student, fee) -> dict:
    """
    Send an SMS fee reminder to the student's emergency contact.

    Args:
        student: Student instance
        fee:     StudentFee instance
    """
    phone = getattr(student, 'emergency_contact', '').strip()
    if not phone:
        return {'error': 'No emergency contact', 'sent': 0}

    if phone.startswith('0') and len(phone) == 10:
        phone = '+233' + phone[1:]
    elif not phone.startswith('+'):
        phone = '+' + phone

    name      = student.user.get_full_name()
    balance   = fee.balance
    head_name = fee.fee_structure.head.name

    msg = (
        f"FEE REMINDER: Dear parent/guardian, {name} has an outstanding "
        f"balance of GHS {balance:.2f} for {head_name}. "
        f"Please make payment at your earliest convenience. Thank you."
    )
    return send_sms([phone], msg)


# ── WhatsApp via Africa's Talking ──────────────────────────────

def send_whatsapp(recipients: list[str], message: str) -> dict:
    """
    Send a WhatsApp message via Africa's Talking.

    Requires the same AT_USERNAME / AT_API_KEY credentials plus a
    WhatsApp-enabled product number (set up in the AT dashboard).

    Args:
        recipients: E.164 phone numbers, e.g. ['+233201234567']
        message:    Plain-text message body

    Returns:
        dict with 'sent' count or 'error'.
    """
    username = getattr(settings, 'AFRICASTALKING_USERNAME', 'sandbox')
    api_key  = getattr(settings, 'AFRICASTALKING_API_KEY',  '')

    if not api_key:
        logger.warning('WhatsApp not sent — AFRICASTALKING_API_KEY is not configured.')
        return {'error': 'AFRICASTALKING_API_KEY not set', 'sent': 0}

    if not recipients:
        return {'error': 'No recipients', 'sent': 0}

    try:
        import africastalking
    except ImportError:
        logger.error('africastalking package not installed.')
        return {'error': 'africastalking package not installed', 'sent': 0}

    try:
        africastalking.initialize(username, api_key)

        # Africa's Talking exposes WhatsApp via requests (REST API)
        # until the SDK adds native support, we call the endpoint directly.
        import requests as req_lib

        url = 'https://content.africastalking.com/version1/whatsapp/send'
        headers = {
            'apiKey': api_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        payload = {
            'username': username,
            'productId': getattr(settings, 'AT_WHATSAPP_PRODUCT_ID', ''),
            'recipients': [{'number': r} for r in recipients],
            'message': {'text': message},
        }

        resp = req_lib.post(url, json=payload, headers=headers, timeout=15)
        data = resp.json()
        logger.info('WhatsApp sent to %d recipients. Response: %s', len(recipients), data)
        return {'sent': len(recipients), 'response': data}

    except Exception as exc:
        logger.exception('WhatsApp sending failed: %s', exc)
        return {'error': str(exc), 'sent': 0}


def _resolve_phone(student) -> str:
    """Normalise student emergency contact to E.164."""
    phone = getattr(student, 'emergency_contact', '').strip()
    if not phone:
        return ''
    if phone.startswith('0') and len(phone) == 10:
        return '+233' + phone[1:]
    if not phone.startswith('+'):
        return '+' + phone
    return phone


def send_whatsapp_attendance_alert(student, status: str, date_str: str) -> dict:
    """WhatsApp attendance alert to parent/guardian."""
    phone = _resolve_phone(student)
    if not phone:
        return {'error': 'No emergency contact', 'sent': 0}

    name = student.user.get_full_name()
    cls_name = student.current_class.name if student.current_class else 'their class'

    if status == 'absent':
        msg = (
            f"📋 *Attendance Alert*\n"
            f"{name} was marked *ABSENT* from {cls_name} on {date_str}.\n"
            f"Please contact the school if this is unexpected."
        )
    elif status == 'late':
        msg = f"📋 *Attendance Alert*\n{name} arrived *LATE* to {cls_name} on {date_str}."
    else:
        msg = f"📋 {name} was marked *PRESENT* in {cls_name} on {date_str}."

    return send_whatsapp([phone], msg)


def send_whatsapp_fee_reminder(student, fee) -> dict:
    """WhatsApp fee payment reminder to parent/guardian."""
    phone = _resolve_phone(student)
    if not phone:
        return {'error': 'No emergency contact', 'sent': 0}

    name = student.user.get_full_name()
    balance = fee.balance
    head_name = fee.fee_structure.head.name

    msg = (
        f"💰 *Fee Reminder*\n"
        f"Dear parent/guardian, {name} has an outstanding "
        f"balance of *GHS {balance:.2f}* for _{head_name}_.\n"
        f"Please make payment at your earliest convenience. Thank you."
    )
    return send_whatsapp([phone], msg)
