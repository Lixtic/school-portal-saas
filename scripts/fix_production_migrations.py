"""
Fix Production Migrations - Apply pending migrations to all tenants
This script connects to the production database and runs migrations.
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

from django.core.management import call_command
from django.db import connection
from tenants.models import School

def fix_production_migrations():
    """Run migrations on production database for all tenants"""
    
    print("=" * 70)
    print("🔧 PRODUCTION MIGRATION FIX".center(70))
    print("=" * 70)
    
    # Check connection
    try:
        connection.ensure_connection()
        print(f"\n✅ Connected to database: {connection.settings_dict['NAME']}")
    except Exception as e:
        print(f"\n❌ Failed to connect to database: {e}")
        sys.exit(1)
    
    try:
        # Step 1: Migrate public schema (shared apps)
        print("\n" + "-" * 70)
        print("📦 Step 1/3: Migrating PUBLIC schema (shared apps)...")
        print("-" * 70)
        call_command('migrate_schemas', '--shared', interactive=False, verbosity=2)
        print("✅ Public schema migrated successfully.\n")
        
        # Step 2: List all tenants
        print("-" * 70)
        print("📋 Step 2/3: Listing all tenant schemas...")
        print("-" * 70)
        
        tenants = School.objects.exclude(schema_name='public').order_by('schema_name')
        if not tenants.exists():
            print("⚠️  No tenants found (excluding public schema).")
        else:
            print(f"Found {tenants.count()} tenant(s):")
            for tenant in tenants:
                print(f"  - {tenant.schema_name} ({tenant.name})")
        
        # Step 3: Migrate all tenant schemas
        print("\n" + "-" * 70)
        print("📦 Step 3/3: Migrating all TENANT schemas...")
        print("-" * 70)
        call_command('migrate_schemas', interactive=False, verbosity=2)
        print("✅ All tenant schemas migrated successfully.\n")
        
        # Verify for GirlsModel specifically
        print("-" * 70)
        print("🔍 Verifying 'GirlsModel' tenant...")
        print("-" * 70)
        
        try:
            girlsmodel = School.objects.get(schema_name='GirlsModel')
            connection.set_tenant(girlsmodel)
            
            # Check if teachers_teacher table exists
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'GirlsModel'
                        AND table_name = 'teachers_teacher'
                    );
                """)
                table_exists = cursor.fetchone()[0]
                
                if table_exists:
                    print("✅ teachers_teacher table exists in GirlsModel schema")
                    
                    # Count teachers
                    cursor.execute('SELECT COUNT(*) FROM teachers_teacher;')
                    count = cursor.fetchone()[0]
                    print(f"   📊 Teacher count: {count}")
                else:
                    print("❌ teachers_teacher table still missing!")
                    print("   Tip: Try running migrations again or check for errors above.")
                    
        except School.DoesNotExist:
            print("⚠️  GirlsModel tenant not found in database.")
        except Exception as e:
            print(f"⚠️  Error checking GirlsModel: {e}")
        
        print("\n" + "=" * 70)
        print("✅ MIGRATION FIX COMPLETED".center(70))
        print("=" * 70)
        print("\n💡 Next steps:")
        print("   1. Test the teachers page: https://school-portal-saas.vercel.app/GirlsModel/teachers/")
        print("   2. If issues persist, trigger a Vercel redeployment")
        print("   3. Check Vercel logs for any migration errors\n")
        
    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ ERROR".center(70))
        print("=" * 70)
        print(f"\nFailed to apply migrations: {e}")
        import traceback
        traceback.print_exc()
        print("\n💡 Troubleshooting:")
        print("   - Ensure DATABASE_URL environment variable is set correctly")
        print("   - Check that you have write permissions to the database")
        print("   - Verify the database is accessible from your network")
        sys.exit(1)

if __name__ == '__main__':
    print("\n⚠️  WARNING: This script will modify the PRODUCTION database!")
    print("    Make sure DATABASE_URL points to production.\n")
    
    # Check if DATABASE_URL is set
    if not os.environ.get('DATABASE_URL'):
        print("❌ DATABASE_URL environment variable not set.")
        print("   Please set it to your Neon production database URL.\n")
        print("   Example:")
        print('   $env:DATABASE_URL="postgresql://user:pass@host/db?sslmode=require"')
        print("   python scripts/fix_production_migrations.py\n")
        sys.exit(1)
    
    response = input("Continue? (yes/no): ")
    if response.lower() in ['yes', 'y']:
        fix_production_migrations()
    else:
        print("❌ Aborted.")
        sys.exit(0)
