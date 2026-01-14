
import os
import sys
import django
from django.core.management import call_command

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

def migrate_remote():
    print("=" * 60)
    print("DJANGO-TENANTS MIGRATION SCRIPT")
    print("=" * 60)
    
    try:
        # Step 1: Migrate public schema (shared apps)
        print("\n[1/2] Migrating PUBLIC schema (shared apps)...")
        print("-" * 60)
        call_command('migrate_schemas', '--shared')
        print("✅ Public schema migrated successfully.")
        
        # Step 2: Migrate all tenant schemas
        print("\n[2/2] Migrating TENANT schemas...")
        print("-" * 60)
        call_command('migrate_schemas')
        print("✅ All tenant schemas migrated successfully.")
        
        print("\n" + "=" * 60)
        print("✅ SUCCESS: All migrations applied successfully.")
        print("=" * 60)
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ ERROR: Failed to apply migrations.")
        print(f"Error details: {e}")
        print("=" * 60)
        sys.exit(1)

if __name__ == '__main__':
    migrate_remote()
