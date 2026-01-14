# 🚨 URGENT: Fix Production Database Issue

## The Problem
Your production site is showing an error because the database tables don't exist yet:
```
relation "tenants_school" does not exist
```

## Quick Fix (5 minutes)

### Step 1: Get Your Neon Database URL
1. Go to https://console.neon.tech/
2. Select your project
3. Click "Connection Details"
4. Copy the connection string (looks like):
   ```
   postgresql://username:password@ep-xxx.region.aws.neon.tech/database
   ```

### Step 2: Set Environment Variable
Open PowerShell and run:
```powershell
$env:DATABASE_URL="paste-your-connection-string-here"
```

### Step 3: Run Migrations
```powershell
python scripts/run_production_migrations.py
```

That's it! Your production site should work now.

## Verification
Visit your site: https://school-portal-saas.vercel.app/
- If you see the homepage → Success! ✅
- If you still see errors → Check the detailed guide below

## Detailed Guides
- [PRODUCTION_MIGRATION_GUIDE.md](PRODUCTION_MIGRATION_GUIDE.md) - Complete migration instructions
- [README.md](README.md) - Project documentation

## What Happened?
When you deployed to Vercel, the Django application code was deployed but the database migrations weren't run automatically. Django needs these migrations to create the database tables that your application uses.

The migration script will:
1. Create the public schema tables (tenants_school, tenants_domain, etc.)
2. Create tables for all apps (students, teachers, academics, etc.)
3. Set up the multi-tenant structure

## Automatic Migrations on Future Deploys
The `build_files.sh` script is now configured to run migrations automatically on each deployment. However, for the initial setup, you need to run migrations manually once.

## Need Help?
- Check Vercel deployment logs: https://vercel.com/your-username/school-portal-saas/deployments
- Review Django logs
- Check if all required environment variables are set in Vercel project settings

## Common Issues

### "fe_sendauth: no password supplied"
- Your DATABASE_URL is missing the password
- Format: `postgresql://user:PASSWORD@host/database`

### "FATAL: no pg_hba.conf entry"
- Add `?sslmode=require` to the end of your connection string
- Example: `postgresql://user:pass@host/db?sslmode=require`

### Script says "DATABASE_URL not set"
- Make sure you're running the command in the same PowerShell window where you set the variable
- Try closing and reopening PowerShell, then set the variable again
