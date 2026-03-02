#!/usr/bin/env python
"""
Migrate a specific tenant schema or all tenants.
Usage: python migrate_tenant.py [schema_name]
If no schema_name provided, migrates all tenants.
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

from django.core.management import call_command
from tenants.models import School

def migrate_tenant(schema_name=None):
    """Migrate specific tenant or all tenants"""
    if schema_name:
        # Migrate specific tenant
        try:
            tenant = School.objects.get(schema_name=schema_name)
            print(f"🔄 Migrating tenant: {tenant.name} (schema: {schema_name})")
            call_command('migrate_schemas', schema_name=schema_name)
            print(f"✅ Successfully migrated {schema_name}")
        except School.DoesNotExist:
            print(f"❌ Error: Tenant with schema_name '{schema_name}' does not exist")
            print("\nAvailable tenants:")
            for school in School.objects.all():
                print(f"  - {school.name} (schema: {school.schema_name})")
            sys.exit(1)
    else:
        # Migrate all tenants
        print("🔄 Migrating all tenant schemas...")
        call_command('migrate_schemas')
        print("✅ Successfully migrated all tenants")

if __name__ == '__main__':
    schema_name = sys.argv[1] if len(sys.argv) > 1 else None
    migrate_tenant(schema_name)
