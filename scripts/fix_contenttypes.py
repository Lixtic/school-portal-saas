"""
Fix stale content types across all tenant schemas.

Django's post_migrate signal creates auth_permissions for content types.
When an app is added/removed from TENANT_APPS, django_content_type rows can
get out of sync with auth_permission, causing FK constraint violations like:

  insert or update on table "auth_permission" violates foreign key constraint
  "auth_permission_content_type_id_2f476e4b_fk_django_co"
  DETAIL: Key (content_type_id)=(54) is not present in table "django_content_type"

This script removes stale content types from every tenant schema and the
public schema so post_migrate re-creates them cleanly.

Run before migrate_schemas in build_files.sh:
  python3 scripts/fix_contenttypes.py
"""
import os
import sys
import django

# Allow running from project root as  python3 scripts/fix_contenttypes.py
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

from django.db import connection
from django_tenants.utils import schema_context, get_public_schema_name
from django.contrib.contenttypes.management import remove_stale_contenttypes
from django.apps import apps

def fix_schema(schema_name):
    with schema_context(schema_name):
        try:
            remove_stale_contenttypes(apps=apps, verbosity=1)
            print(f"  ✓ {schema_name}: stale content types removed")
        except Exception as exc:
            print(f"  ⚠ {schema_name}: {exc}")

def main():
    from tenants.models import School

    print("=== Removing stale content types ===")

    # Public schema first
    fix_schema(get_public_schema_name())

    # All tenant schemas
    for school in School.objects.exclude(schema_name=get_public_schema_name()):
        fix_schema(school.schema_name)

    print("=== Done ===")

if __name__ == '__main__':
    main()
