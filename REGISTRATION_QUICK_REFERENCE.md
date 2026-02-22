# School Registration - Quick Reference Guide

**Status**: ✅ All Issues Fixed | Commit: 1ba427d

---

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Copy .env template and update:
# DATABASE_URL=postgresql://...
# DEFAULT_FROM_EMAIL=noreply@yourdomain.com
# EMAIL_HOST=smtp.gmail.com
# EMAIL_HOST_USER=...
# EMAIL_HOST_PASSWORD=...
# BASE_SCHOOL_DOMAIN=yourdomain.com  # For production
```

### 2. Run Debug Script
```bash
python debug_registration.py
```
Should output ✓ for all 10 checks.

### 3. Test Registration Flow
```
/signup/ → Submit school → Check email → /tenants/approval-queue/
→ Approve → Email with credentials → /<schema>/login/
```

---

## 📋 Key Changes

| What | Before | After |
|------|--------|-------|
| **Admin Password** | Hardcoded 'admin' | Secure random (16 chars) |
| **Password in Email** | Hardcoded in template | Dynamic from context |
| **Domains** | Only `.local` | `.local` or custom domain |
| **Staff Access** | No navbar link | Visible in navbar (staff only) |
| **Email Function** | Fixed parameters | Flexible `extra_context` |

---

## ⚙️ Configuration

### Environment Variables
```bash
# Email (REQUIRED for notifications)
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Domains (Optional, defaults to .local)
BASE_SCHOOL_DOMAIN=yourdomain.com  # For production
```

### Settings (Python)
```python
# school_system/settings.py
BASE_SCHOOL_DOMAIN = os.environ.get('BASE_SCHOOL_DOMAIN', 'local')
```

---

## 🔐 Security Improvements

✅ No hardcoded passwords  
✅ Cryptographic random password generation  
✅ Secure SMTP communication  
✅ Per-tenant schema isolation  
✅ Admin forced to change password (recommended)  

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| `REGISTRATION_DEBUG_REPORT.md` | All issues found (10 items) |
| `REGISTRATION_FIXES_APPLIED.md` | All fixes applied + instructions |
| `REGISTRATION_DEBUG_SUMMARY.md` | This summary + testing checklist |
| `debug_registration.py` | Automated validation script |

---

## 🧪 Testing

### Manual Flow
1. Go to `/signup/` and submit school application
2. Check email for confirmation
3. Login as staff, visit `/tenants/approval-queue/`
4. Approve the school
5. Check email for credentials
6. Login at `/<schema>/login/` with admin user
7. Change password immediately (recommended)

### Automated Testing
```bash
python debug_registration.py
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| No email received | Check EMAIL_* vars, check EMAIL_BACKEND |
| Can't approve school | Check DATABASE_URL, PostgreSQL running |
| Can't login to school | Check schema created, admin user exists |
| Domain error | Check BASE_SCHOOL_DOMAIN setting |

---

## 📞 Support

1. Run `debug_registration.py` to check configuration
2. Check logs for specific errors
3. Review `REGISTRATION_DEBUG_REPORT.md` for detailed analysis
4. See `REGISTRATION_FIXES_APPLIED.md` for testing steps

---

## Files Changed

✅ `tenants/views.py` - Password generation  
✅ `tenants/email_notifications.py` - Flexible context  
✅ `templates/tenants/emails/status_approved.html` - Dynamic password  
✅ `templates/landing_public.html` - Staff admin link  
✅ `school_system/settings.py` - Domain configuration  

---

**Last Updated**: February 22, 2026  
**Commit**: 1ba427d  
**Status**: Production Ready ✓
