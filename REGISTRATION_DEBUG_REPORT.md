# School Registration Flow - Debug Report

**Date**: February 22, 2026  
**Status**: Initial Assessment Complete

## Registration Flow Overview

The school registration system has a **2-stage approval workflow**:
1. **Signup (Public)** → Tenant created in `pending` status
2. **Admin Approval** → Schema created, activated, sample data loaded

---

## Current Flow

```
User submits form on /signup/
    ↓
SchoolSignupForm validates:
  - Schema name (lowercase, no spaces, not reserved)
  - School details (name, type, address, phone)
  - Contact person info (name, email, phone, title)
  - Verification documents (registration_certificate required)
    ↓
school_signup() view processes:
  - Creates School record with status='pending'
  - Creates Domain record (schema_name.local)
  - Sends confirmation email to contact_person_email
  - Shows signup_success.html
    ↓
Admin visits /tenants/approval-queue/
  - Reviews pending schools
  - Opens school detail at /tenants/review/<school_id>/
    ↓
Admin submits approval form:
  - Changes status to 'approved'
  - System auto-creates schema
  - Creates admin user (username='admin', password='admin')
  - Loads sample data (AcademicYear, Classes, Subjects, etc.)
  - Sends approval email
    ↓
School admin logs in at /<schema_name>/login/
  - Authenticated within tenant schema
  - Accesses dashboard, can configure school
```

---

## Identified Issues & Gaps

### 1. ❌ **Missing Email Templates**
**Severity**: HIGH  
**Location**: `tenants/email_notifications.py` expects templates that may not exist

**Templates Referenced**:
- `tenants/emails/submission_confirmation.html` - ✓ Need to verify exists
- `tenants/emails/status_pending.html` - Status update emails
- `tenants/emails/status_approved.html` - Approval notification
- `tenants/emails/status_rejected.html` - Rejection notification
- `tenants/emails/status_requires_info.html` - More info needed
- `tenants/emails/status_under_review.html` - Status update

**Fix Required**: Create missing email templates in `templates/tenants/emails/`

---

### 2. ⚠️ **File Upload Storage**
**Severity**: MEDIUM  
**Location**: `tenants/models.py` and `/tenants/views.py`

**Issues**:
- Documents uploaded to `school_credentials/` directories
- In production (Cloudinary), this may need special handling
- No validation of file extensions beyond basic checks
- Files are required but error handling unclear

**Recommendations**:
1. Add better error handling in `school_signup()` for file upload failures
2. Ensure Cloudinary is configured for `school_credentials/` path
3. Add file size validation feedback to user

---

### 3. 🔐 **Hardcoded Admin Credentials**
**Severity**: CRITICAL  
**Location**: `tenants/views.py`, line 323

```python
admin_user = User.objects.create_superuser(
    username='admin',
    email=temp_email,
    password='admin',  # ← HARDCODED!
    user_type='admin'
)
```

**Issues**:
- Password is hardcoded as 'admin'
- No notification to school about initial credentials
- No password reset flow documented
- Security risk if database is compromised

**Fix**:
- Generate random password using `secrets.token_urlsafe(12)`
- Send password in approval email (one-time setup link)
- Or require password reset on first login

---

### 4. ❌ **Missing "Landlord Dashboard" Link**
**Severity**: MEDIUM  
**Location**: `school_system/urls.py` - no public-facing admin link

**Issue**: 
- Staff can't access `/tenants/landlord/` from public site
- No login/admin access UI for platform admins
- Approval workflow hidden

**Fix**: Add staff/admin access link to public homepage

---

### 5. 📧 **Email Configuration Assumptions**
**Severity**: MEDIUM  
**Location**: `tenants/email_notifications.py`

**Issues**:
- Assumes `settings.DEFAULT_FROM_EMAIL` is configured
- No fallback if email sending fails (only logs error)
- No retry mechanism for failed emails

**Environment Variables Needed**:
```
DEFAULT_FROM_EMAIL=noreply@school-portal.com
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...
```

---

### 6. 🔗 **Domain Creation Hardcoded**
**Severity**: MEDIUM  
**Location**: `tenants/views.py`, line 68

```python
domain = Domain()
domain.domain = f"{schema_name}.local"  # ← Hardcoded .local!
```

**Issue**: 
- Production should use actual domain (e.g., `school1.schoolportal.com`)
- `.local` only works for local testing
- No configuration for multi-domain setup

**Fix**:
```python
BASE_DOMAIN = getenv('BASE_DOMAIN', 'schoolportal.com')
domain.domain = f"{schema_name}.{BASE_DOMAIN}"
```

---

### 7. ❌ **Schema Migration on Approval**
**Severity**: HIGH  
**Location**: `tenants/views.py`, line 318-322

**Issues**:
- `school.create_schema()` may fail silently
- If migration fails, school is marked as approved but not functional
- No rollback if sample data creation fails
- Error handling is basic

**Current Code**:
```python
try:
    school.save()
    school.create_schema(check_if_exists=True, verbosity=1)
    connection.set_tenant(school)
    # ... create admin user and sample data ...
except Exception as e:
    # Only logs error, sets status to 'requires_info'
    connection.set_schema_to_public()
```

**Improvement**:
- Use database transaction for schema + admin + data creation
- Better error reporting to admin
- Option to retry approval

---

### 8. 🔔 **No Status Change Notifications to School**
**Severity**: LOW  
**Location**: `tenants/views.py`

**Issue**:
- Only sends email on approval
- No notification for 'pending' status (automatic on signup)
- School doesn't know if under_review or requires_info

**Fix**: Send email notifications for all status changes

---

### 9. 📋 **Missing Form Validation Feedback**
**Severity**: LOW  
**Location**: `tenants/forms.py`

**Issues**:
- schema_name must be lowercase (enforced)
- But error messages could be clearer
- No duplicate domain check

**Example Error Messages**:
```
- "School ID must contain only lowercase letters and numbers (no spaces)."
- "The School ID 'schoolname' is already taken."
```

These are good, but could link to documentation.

---

### 10. 🚀 **Sample Data Creation Incomplete**
**Severity**: MEDIUM  
**Location**: `tenants/views.py`, `_create_sample_data()` function

**Issues**:
- Creates AcademicYear, Classes, Subjects but may not complete
- No validation that sample data was created
- Orphaned tenant if creation fails partway
- No way to re-generate or customize sample data

---

## Database Schema

### Key Tables in PUBLIC schema:
- `tenants_school` - School records with approval_status
- `tenants_domain` - Domain mappings
- `tenants_schoolsubscription` - (from subscription_models)
- `tenants_supportticket` - Support/help system

### Key Tables in TENANT schema (created per school):
- `accounts_user` - Users within that school
- `academics_*` - Academic data (classes, subjects, etc.)
- `students_*` - Student records
- `teachers_*` - Teacher records
- etc.

---

## Testing the Registration Flow

### Manual Testing Steps:

1. **Start Dev Server**
   ```bash
   python manage.py runserver
   ```

2. **Visit Public Site**
   ```
   http://localhost:8000/
   ```

3. **Navigate to Signup**
   ```
   Click "Start Your School's Journey" or go to /signup/
   ```

4. **Submit Test School**
   - School Name: "Test School XYZ"
   - Schema: "testxyz"
   - Contact: Your email
   - Upload any file as "registration_certificate"
   - Submit

5. **Check Pending Schools** (as superuser/staff)
   ```
   http://localhost:8000/tenants/approval-queue/
   ```

6. **Approve School**
   - Click school name
   - Change status to "Approved"
   - Submit
   - Check console for errors

7. **Login to Tenant**
   ```
   http://localhost:8000/testxyz/login/
   Username: admin
   Password: admin
   ```

---

## Run Debug Script

```bash
python debug_registration.py
```

**This will check**:
- Database connectivity
- School model fields
- Tenant creation
- Domain creation
- Schema creation capability
- Orphaned schemas (DB schemas without tenant records)
- Pending/Approved school summary

---

## Recommended Fixes (Priority Order)

### 🔴 CRITICAL (Do First):
1. **Fix hardcoded admin password** - Use random password + email
2. **Create missing email templates** - Schools need confirmation emails
3. **Add schema creation error handling** - Prevent broken approvals

### 🟠 HIGH (Do Next):
4. **Add staff admin access UI** - Platform admins need easy access
5. **Fix domain configuration** - Support production domains
6. **Add rollback on failure** - Clean up orphaned tenants

### 🟡 MEDIUM (Nice to Have):
7. **Email configuration docs** - Document EMAIL_* settings
8. **Improve error messages** - Better feedback for failed approvals
9. **Sample data validation** - Ensure it's created correctly

### 🟢 LOW (Polish):
10. **Status notifications** - Notify school of all status changes
11. **Domain duplicate check** - Prevent domain conflicts
12. **Re-generate sample data** - Admin option to reset

---

## Environment Variables Checklist

For registration to work in production:

```bash
# Email Configuration (REQUIRED)
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Domain Configuration (REQUIRED)
BASE_DOMAIN=schoolportal.yourdomain.com  # Or your actual domain

# Database (REQUIRED)
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Django (REQUIRED)
SECRET_KEY=your-secret-key
DEBUG=False

# Cloudinary (For Media - OPTIONAL but recommended)
CLOUDINARY_CLOUD_NAME=...
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...
```

---

## Next Steps

1. ✅ Run `debug_registration.py` to identify environment-specific issues
2. ✅ Create email templates
3. ✅ Fix hardcoded admin password
4. ✅ Test full signup → approval → login flow
5. ✅ Add staff access UI to public site
6. ✅ Document in README

