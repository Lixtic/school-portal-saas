# Tenant Migration Guide

## Understanding the Issue

When using django-tenants with PostgreSQL, each school (tenant) has its own isolated database schema. When a new tenant is created:

1. ✅ The schema is automatically created (`auto_create_schema = True`)
2. ❌ Tables are NOT automatically created (migrations not run)
3. ❌ Accessing the tenant results in "relation does not exist" errors

## Solutions

### For Development (Local)

When a new tenant is created locally, run:

```bash
# Migrate specific tenant
python manage.py migrate_schemas --schema=SCHEMA_NAME

# Or migrate all tenants
python manage.py migrate_schemas
```

Or use the utility script:

```bash
# Migrate specific tenant
python migrate_tenant.py SCHEMA_NAME

# Migrate all tenants
python migrate_tenant.py
```

### For Production (Vercel/Railway)

**Option 1: Trigger Deployment (Recommended)**

After creating a new tenant in production:

```bash
git commit --allow-empty -m "Migrate new tenant"
git push origin main
```

This triggers a deployment that runs:
- `migrate_schemas --shared` (public schema)
- `migrate_schemas` (all tenant schemas)

**Option 2: Manual Migration via Database Connection**

If you have direct database access:

```bash
# Connect to production database
export DATABASE_URL="your_neon_connection_string"

# Run migrations
python manage.py migrate_schemas --schema=SCHEMA_NAME
```

## Prevention Strategies

### 1. Bulk Tenant Creation

If creating multiple tenants, do it BEFORE deployment:

```python
# Create all tenants
School.objects.create(schema_name='school1', name='School 1')
School.objects.create(schema_name='school2', name='School 2')

# Then deploy (migrations run for all)
git push origin main
```

### 2. Admin Workflow

When approving schools in the admin panel:
1. Approve school (creates tenant schema)
2. Trigger deployment to run migrations
3. Notify school that setup is complete

### 3. Scheduled Migrations (Advanced)

For high-frequency tenant creation, consider:
- Scheduled job that runs `migrate_schemas` every hour
- Migration queue system
- Separate migration service

## Build Process

Our `build_files.sh` automatically runs:

```bash
# Public schema (shared apps)
python3 manage.py migrate_schemas --shared

# All tenant schemas
python3 manage.py migrate_schemas
```

This ensures all tenants are migrated on every deployment.

## Common Errors

### "relation does not exist"

**Cause:** Tenant schema exists but tables haven't been created.

**Solution:** Run migrations for that tenant (see above).

### "schema does not exist"

**Cause:** Tenant record exists but schema wasn't created.

**Solution:** 
```python
from tenants.models import School
tenant = School.objects.get(schema_name='SCHEMA_NAME')
tenant.create_schema()  # Manually create schema
# Then run migrations
```

## Utility Script Usage

The `migrate_tenant.py` script provides easy tenant migration:

```bash
# List all tenants and migrate specific one
python migrate_tenant.py school1

# Migrate all tenants
python migrate_tenant.py

# View available tenants if you forget schema_name
# (script will show them if you provide wrong name)
python migrate_tenant.py wrong_name
```

## Best Practices

1. ✅ Create tenants in bulk when possible
2. ✅ Trigger deployment immediately after tenant creation in production
3. ✅ Test tenant creation flow in staging environment
4. ✅ Monitor tenant schema status
5. ✅ Document new tenant creation process for your team
6. ❌ Don't create tenants during high-traffic periods
7. ❌ Don't assume migrations run automatically in serverless environments
