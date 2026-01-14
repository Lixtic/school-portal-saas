# Production Database Migration Guide

## Problem
The production database on Neon doesn't have the required tables yet, causing the error:
```
relation "tenants_school" does not exist
```

## Solution: Run Migrations Against Production Database

### Method 1: Run Locally Against Production DB (Recommended)

1. **Set your DATABASE_URL environment variable** to point to your Neon database:
   ```powershell
   $env:DATABASE_URL="your-neon-connection-string"
   ```

2. **Run the migration script**:
   ```powershell
   python scripts/migrate_remote.py
   ```

   This will:
   - Migrate the public schema (creates `tenants_school` and other shared tables)
   - Migrate all existing tenant schemas

### Method 2: Vercel Build Script (Automatic on Deploy)

Your `build_files.sh` already includes the migration commands:
```bash
python3 manage.py migrate_schemas --shared
python3 manage.py migrate_schemas
python3 scripts/setup_tenants.py
```

This should run automatically on deployment. If it didn't work, it might be because:
- The build script failed silently
- Vercel didn't execute the script
- There's a configuration issue

### Method 3: Manual Migration Commands

If you need to run migrations manually:

1. **Connect to production database**:
   ```powershell
   $env:DATABASE_URL="your-neon-connection-string"
   ```

2. **Run migration commands**:
   ```powershell
   # Migrate public schema first
   python manage.py migrate_schemas --shared
   
   # Then migrate all tenant schemas
   python manage.py migrate_schemas
   ```

3. **Set up tenants** (if needed):
   ```powershell
   python scripts/setup_tenants.py
   ```

## Verification

After running migrations, verify by checking:

1. **Public schema tables exist**:
   - `tenants_school`
   - `tenants_domain`
   - `django_content_type`
   - etc.

2. **Your production site loads** without the "relation does not exist" error

## Getting Your Neon Connection String

1. Go to your Neon Console: https://console.neon.tech/
2. Select your project
3. Go to "Connection Details"
4. Copy the connection string (should look like):
   ```
   postgresql://user:password@ep-xxx-xxx.region.aws.neon.tech/database?sslmode=require
   ```

## Troubleshooting

### Error: "fe_sendauth: no password supplied"
- Make sure your DATABASE_URL includes the password
- Format: `postgresql://user:password@host/database`

### Error: "relation already exists"
- This means migrations were partially run
- Run `python manage.py migrate_schemas --fake` if needed

### Build script not running on Vercel
- Check `vercel.json` to ensure `build_files.sh` is being executed
- Check Vercel deployment logs for errors
- You may need to add execution permissions: `chmod +x build_files.sh`

## Next Steps After Migration

Once migrations are complete, your production site should work. You can then:

1. **Create school tenants** via the signup page
2. **Create superuser** for each tenant:
   ```powershell
   python manage.py createsuperuser --schema=your_school_name
   ```
3. **Load sample data** (if needed) for specific tenants
