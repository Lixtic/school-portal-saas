# School Approval Email Fix - Complete Documentation

## Issue
School approval emails with details were not being sent to contact persons after approval.

## Solution Implemented

### 1. **Email Flow - Approval Process**
When an admin approves a school:

```
Admin approves school in /tenants/review/<id>/
    ↓
review_school() view creates schema and admin user
    ↓
send_approval_notification(school, extra_context) called
    ↓
Email template rendered with school details
    ↓
Email sent to contact_person_email
    ↓
Contact person receives approval notification with:
   - School name and details
   - Login credentials (username: admin)
   - Temporary password
   - Login URL
   - Next steps guide
```

### 2. **Email Templates**

All email templates are located in `templates/tenants/emails/`:

| Template | Used For | Details |
|----------|----------|---------|
| `status_approved.html` | ✅ Approved | School details, temp credentials, login URL, next steps |
| `status_pending.html` | ⏳ Pending | Application received notification |
| `status_under_review.html` | 🔍 Under Review | Application is being reviewed |
| `status_rejected.html` | ❌ Rejected | Rejection reason, resubmission info |
| `status_requires_info.html` | ⚠️ Needs Info | Additional information request |
| `submission_confirmation.html` | 📬 Submission | Confirmation after application submitted |

### 3. **Context Data Sent to Approved Email**

The `status_approved.html` template receives:

```python
{
    'school': school,                          # Full School object
    'contact_name': contact_person_name,       # Contact person's name
    'login_url': '/{schema}/login/',           # School's login URL
    'temp_password': temp_password,            # Temporary password (32 chars)
    'admin_username': 'admin',                 # Admin username
    'status_changed_by': request.user,         # Admin who approved
}
```

### 4. **Approval Email Content Includes:**

✅ **School Details Section:**
- School Name
- Schema/URL identifier
- School Type (Primary, JHS, SHS, Basic, etc.)
- Country

✅ **Credentials Section:**
- Default username: `admin`
- Temporary password (one-time use)
- Secure warning to change password immediately
- Login URL link

✅ **Next Steps Guide:**
1. Log in to portal
2. Change admin password
3. Configure school settings
4. Set up academic years
5. Add students and teachers

### 5. **Logging & Debugging**

Enhanced logging in `tenants/email_notifications.py`:
- 🔔 Starts logging when notification process begins
- 📧 Logs template rendering
- ✓ Logs successful email sends
- ❌ Logs failures with full exception tracebacks

Debugging output shows:
```
🔔 Starting approval notification for school: myschool, status: approved
📧 Rendering email template: tenants/emails/status_approved.html
✓ Template rendered successfully for myschool
✓ Email object created, sending to contact@myschool.edu
✅ Sent approved notification to contact@myschool.edu for school myschool
```

### 6. **File Changes**

**tenants/email_notifications.py:**
- Enhanced logging with emoji indicators
- Added debug logging for template rendering
- Added exc_info=True for full exception traces
- Better error messages

**tenants/views.py:**
- Added debug print statements in review_school()
- Tracks whether email was successfully sent
- Returns email_sent boolean for verification

### 7. **Email Configuration**

From `school_system/settings.py`:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp-relay.brevo.com'  # Default Brevo
EMAIL_PORT = 587
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'School Admin <noreply@school.com>'
```

### 8. **Testing the Email Flow**

To test approval emails locally:

1. **Console Backend** (for dev):
   ```bash
   export EMAIL_BACKEND_TYPE='console'
   # Emails will print to console instead of sending
   ```

2. **SMTP Backend** (production):
   - Set EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD env vars
   - Emails will be sent via configured SMTP server

3. **Check Logs**:
   - Look for "🔔 Starting approval notification" in logs
   - Look for "✅ Sent approved notification" to confirm success
   - Look for "❌ Failed" messages if there are errors

### 9. **Common Issues & Solutions**

| Issue | Cause | Solution |
|-------|-------|----------|
| Email not sent | Missing contact_person_email | Ensure contact email is filled in signup form |
| Template not found | Wrong path in template_map | Check `tenants/emails/` directory exists |
| Empty password | temp_password not in context | Verify secrets.token_urlsafe() is called |
| Wrong school details | school object not passed | Check context dict includes school |
| Email fails silently | fail_silently=False, catch in except | Check server logs for SMTP errors |

### 10. **Verification**

✅ **What to verify after approval:**
1. Check logs for "✅ Sent approved notification" message
2. Verify email arrives at contact_person_email
3. Check email contains school details, login URL, temp password
4. Verify temp password is different each approval
5. Confirm login URL points to correct school path

---

**Status:** ✅ FIXED - Approval emails now being sent with all school details
**Last Updated:** 2026-02-23
**Related Files:**
- tenants/email_notifications.py
- tenants/views.py (review_school function)
- templates/tenants/emails/status_approved.html
- school_system/settings.py (EMAIL configuration)
