"""
Run migrations on production (Neon) database for all tenant schemas.
This script connects to the remote database and applies pending migrations.
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')

# Ensure we're using production database
if not os.environ.get('DATABASE_URL'):
    print("ERROR: DATABASE_URL environment variable not set!")
    print("Please set it to your Neon database connection string.")
    sys.exit(1)

django.setup()

from django.core.management import call_command
from tenants.models import School

def run_migrations():
    print("=" * 70)
    print("PRODUCTION DATABASE MIGRATION SCRIPT")
    print("=" * 70)
    
    try:
        # Step 1: Show database info
        from django.conf import settings
        db_name = settings.DATABASES['default']['NAME']
        db_host = settings.DATABASES['default']['HOST']
        print(f"\nConnected to: {db_host}")
        print(f"Database: {db_name[:50]}..." if len(db_name) > 50 else f"Database: {db_name}")
        
        # Step 2: Count tenants
        tenant_count = School.objects.all().count()
        print(f"\nFound {tenant_count} tenant(s) to migrate")
        
        if tenant_count == 0:
            print("\n⚠️  WARNING: No tenants found. Creating schemas for existing tenants...")
        
        # Step 3: Migrate shared schema
        print("\n" + "-" * 70)
        print("[1/2] Migrating SHARED/PUBLIC schema...")
        print("-" * 70)
        call_command('migrate', '--database=default', interactive=False)
        print("✅ Public schema migrated")
        
        # Step 4: Migrate each tenant individually
        print("\n" + "-" * 70)
        print(f"[2/2] Migrating {tenant_count} TENANT schema(s)...")
        print("-" * 70)
        
        for school in School.objects.all():
            print(f"\n  → Migrating tenant: {school.schema_name} ({school.name})")
            try:
                # Set the schema for this tenant
                from django.db import connection
                connection.set_schema(school.schema_name)
                
                # Run migrations for this tenant
                call_command('migrate', '--database=default', interactive=False)
                print(f"    ✅ {school.schema_name} migrated successfully")
                
            except Exception as e:
                print(f"    ⚠️  Error migrating {school.schema_name}: {str(e)}")
                continue
        
        # Reset to public schema
        connection.set_schema_to_public()
        
        print("\n" + "=" * 70)
        print("✅ MIGRATION COMPLETED")
        print("=" * 70)
        
    except Exception as e:
        print("\n" + "=" * 70)
        print(f"❌ ERROR: Migration failed")
        print(f"Details: {str(e)}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    run_migrations()
