# Email Notification Configuration Guide

## Overview
The school approval workflow automatically sends email notifications for:
- ✅ **Submission Confirmation** - Immediately after school registers
- 🔍 **Under Review** - When admin marks application as under review
- ✔️ **Approved** - When school is approved (includes login credentials)
- ❌ **Rejected** - When application is rejected (includes reason)
- ⚠️ **Requires Info** - When additional documents/info needed

## Local Development (Console Mode)

For testing without real email sending, emails print to terminal:

```bash
# Windows PowerShell
$env:EMAIL_BACKEND_TYPE='console'
python manage.py runserver

# Linux/Mac
export EMAIL_BACKEND_TYPE=console
python manage.py runserver
```

Run test script:
```bash
python test_email.py
```

## Production Setup

### Option 1: Brevo (Recommended - Free tier available)

1. **Sign up at**: https://www.brevo.com/
2. **Get SMTP credentials** from Settings → SMTP & API
3. **Set environment variables**:

```bash
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_brevo_login_email
EMAIL_HOST_PASSWORD=your_smtp_key
DEFAULT_FROM_EMAIL=School Portal <noreply@yourdomain.com>
```

### Option 2: Gmail SMTP

1. **Enable 2FA** on your Gmail account
2. **Create App Password**: Google Account → Security → 2-Step Verification → App passwords
3. **Set environment variables**:

```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
DEFAULT_FROM_EMAIL=School Portal <your_email@gmail.com>
```

### Option 3: SendGrid

```bash
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your_sendgrid_api_key
DEFAULT_FROM_EMAIL=School Portal <verified_sender@yourdomain.com>
```

### Option 4: AWS SES

```bash
EMAIL_HOST=email-smtp.us-east-1.amazonaws.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_ses_smtp_username
EMAIL_HOST_PASSWORD=your_ses_smtp_password
DEFAULT_FROM_EMAIL=School Portal <verified@yourdomain.com>
```

## Vercel Environment Variables

Add these in Vercel Dashboard → Project → Settings → Environment Variables:

```
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_username
EMAIL_HOST_PASSWORD=your_password
DEFAULT_FROM_EMAIL=School Portal <noreply@yourdomain.com>
```

**Important**: Do NOT set `EMAIL_BACKEND_TYPE` in production (it defaults to SMTP).

## Customizing Email Templates

Templates are located in: `templates/tenants/emails/`

- `submission_confirmation.html` - Initial confirmation
- `status_pending.html` - Pending review reminder
- `status_under_review.html` - Review in progress
- `status_approved.html` - Approval with credentials
- `status_rejected.html` - Rejection with reason
- `status_requires_info.html` - Request for more info

Edit these files to customize branding, colors, or messaging.

## Troubleshooting

### Emails not sending in production?

1. **Check logs** for error messages:
   ```bash
   vercel logs <your-deployment-url>
   ```

2. **Verify environment variables** are set correctly

3. **Test SMTP credentials** manually:
   ```python
   python manage.py shell
   from django.core.mail import send_mail
   send_mail('Test', 'Message', 'from@example.com', ['to@example.com'])
   ```

4. **Common issues**:
   - Gmail: Ensure App Password is used (not regular password)
   - Brevo: Verify email address in Brevo dashboard
   - SendGrid: Use verified sender identity
   - All: Check firewall allows outbound port 587

### Emails going to spam?

1. **Use verified domain** for FROM address
2. **Add SPF/DKIM records** (provided by email service)
3. **Don't use "noreply@gmail.com"** - use your domain
4. **Test with mail-tester.com** to check spam score

## Code Reference

**Email notification functions**: `tenants/email_notifications.py`
- `send_submission_confirmation(school)` - Called on signup
- `send_approval_notification(school, status_changed_by)` - Called on status change

**Integration points**:
- `tenants/views.py:school_signup` - Line ~67 (sends submission confirmation)
- `tenants/views.py:review_school` - Lines ~310, ~318, ~322 (sends status updates)

## Email Delivery Monitoring

To track email delivery in production, most services provide dashboards:
- **Brevo**: Statistics → Email → Transactional
- **SendGrid**: Activity Feed
- **AWS SES**: Email Sending → Sending Statistics
- **Gmail**: Admin console (G Suite only)

## Rate Limits

Free tier limits (as of 2024):
- **Brevo**: 300 emails/day
- **SendGrid**: 100 emails/day
- **Gmail**: 500 emails/day (2000 for G Suite)
- **AWS SES**: 200 emails/day (then pay-as-you-go)

For high-volume schools (100+ signups/day), upgrade to paid plans.
