# Production Migration Fix Guide

## Issue
```
ProgrammingError: relation "teachers_teacher" does not exist
```

This error occurs when database migrations haven't been applied to tenant schemas on production.

## Quick Fixes (Choose One)

### Option 1: Trigger Vercel Redeployment (Easiest) ⭐

The `wsgi.py` file automatically runs migrations on startup. Force a redeployment:

1. **Via Vercel Dashboard:**
   - Go to your project on Vercel
   - Click "Deployments" tab
   - Find the latest deployment
   - Click "..." → "Redeploy"

2. **Via Git (Quick):**
   ```bash
   git commit --allow-empty -m "trigger migration deployment"
   git push origin main
   ```

3. **Check deployment logs:**
   - Look for: `>>> WSGI: Migrations applied successfully.`
   - If you see migration errors, proceed to Option 2

---

### Option 2: Run Migration Script Manually

Use the provided script to migrate production database:

#### Prerequisites:
- Python virtual environment activated
- Production `DATABASE_URL` from Neon Console

#### Steps:

1. **Get your Neon DATABASE_URL:**
   - Go to [Neon Console](https://console.neon.tech/)
   - Select your project
   - Copy the connection string (should look like):
     ```
     postgresql://username:password@hostname.neon.tech/dbname?sslmode=require
     ```

2. **Set environment variable and run script:**

   **Windows PowerShell:**
   ```powershell
   $env:DATABASE_URL="postgresql://your-connection-string"
   python scripts/fix_production_migrations.py
   ```

   **Linux/Mac:**
   ```bash
   export DATABASE_URL="postgresql://your-connection-string"
   python scripts/fix_production_migrations.py
   ```

3. **The script will:**
   - ✅ Migrate public schema
   - ✅ Migrate all tenant schemas (including GirlsModel)
   - ✅ Verify teachers_teacher table exists
   - ✅ Show teacher count

---

### Option 3: Manual Migration Commands

If you have SSH/shell access to production:

```bash
# Activate environment
source venv/bin/activate  # or equivalent

# Run migrations
python manage.py migrate_schemas --shared
python manage.py migrate_schemas

# Verify for specific tenant
python manage.py tenant_command migrate --schema=GirlsModel
```

---

## Verify the Fix

After running migrations, test the teachers page:
```
https://school-portal-saas.vercel.app/GirlsModel/teachers/
```

Should load without errors ✅

---

## Why This Happened

The `teachers` app is in `TENANT_APPS`, which means each tenant gets its own `teachers_teacher` table. When:
- A new tenant is created manually (not via signup flow)
- Migrations are added but not deployed properly
- Vercel serverless cold starts don't complete migration

The migrations need to be re-run for all tenant schemas.

---

## Prevention

### Automatic Migrations on Deployment

The project is configured to auto-migrate via `wsgi.py`. This should work for most deployments, but serverless platforms like Vercel can have timing issues.

### For New Tenants

When creating tenants manually, always ensure migrations run:

```python
# In scripts/setup_tenants.py or similar
from tenants.models import School

# After creating tenant
new_school = School.objects.create(
    schema_name='newschool',
    name='New School',
    auto_create_schema=True  # ← This triggers migrations
)
```

---

## Troubleshooting

### Migration script fails with "permission denied"
- Ensure DATABASE_URL has write permissions
- Check firewall/network allows connection to Neon

### "GirlsModel tenant not found"
- Verify tenant exists in public schema:
  ```python
  from tenants.models import School
  School.objects.filter(schema_name='GirlsModel').exists()
  ```

### Other tables missing (not just teachers)
- Run full migration: `python manage.py migrate_schemas`
- Check for migration errors in Vercel logs

### Still getting errors after migration
- Clear browser cache and cookies
- Check if other tenant-specific tables are missing
- Review Vercel deployment logs for errors

---

## Need Help?

Check the logs:
- **Local development:** Terminal output when running `python manage.py runserver`
- **Vercel production:** Project → Deployments → Click deployment → "View Function Logs"

Look for:
- `>>> WSGI: Running migrate_schemas`
- `>>> WSGI: Migrations applied successfully`
- Any Django database errors
