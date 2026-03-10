"""
Diagnose and fix missing migrations in all tenant schemas.
Compares django_migrations records between public and each tenant,
then applies the DDL for any missing academics/students/teachers migrations.
"""
import os, sys, django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

from django.db import connection
from django.core.management import call_command
from django_tenants.utils import schema_context
from tenants.models import School

# ── 1. Get the full set of expected migrations from public schema ──
with connection.cursor() as cur:
    cur.execute(
        "SELECT app, name FROM django_migrations ORDER BY app, name"
    )
    public_migrations = set(cur.fetchall())

print(f"Public schema has {len(public_migrations)} migration records.\n")

# ── 2. For each tenant, find + apply missing ones ──
tenants = list(School.objects.exclude(schema_name='public'))
print(f"Tenants: {[t.schema_name for t in tenants]}\n")

for tenant in tenants:
    schema = tenant.schema_name
    print(f"{'='*60}")
    print(f"Tenant: {schema}")

    with schema_context(schema):
        with connection.cursor() as cur:
            cur.execute("SELECT app, name FROM django_migrations ORDER BY app, name")
            tenant_migrations = set(cur.fetchall())

        missing = sorted(public_migrations - tenant_migrations)
        if not missing:
            print(f"  All migrations present — skipping.")
            continue

        print(f"  Missing {len(missing)} migration(s):")
        for m in missing:
            print(f"    - {m[0]}.{m[1]}")

        # Try migrate_schemas for this tenant
        print(f"\n  Running migrate_schemas for schema '{schema}'...")
        try:
            call_command('migrate_schemas', f'--schema={schema}', verbosity=1)
            print(f"  migrate_schemas completed for {schema}.")
        except Exception as e:
            print(f"  migrate_schemas hit an error: {e}")
            print(f"  Will try marking already-handled migrations manually...")

            with schema_context(schema):
                with connection.cursor() as cur:
                    # Re-check what's still missing after partial run
                    cur.execute("SELECT app, name FROM django_migrations ORDER BY app, name")
                    tenant_migrations_after = set(cur.fetchall())
                    still_missing = sorted(public_migrations - tenant_migrations_after)
                    print(f"  Still missing after migrate_schemas attempt: {len(still_missing)}")
                    for m in still_missing:
                        print(f"    - {m[0]}.{m[1]}")

print(f"\n{'='*60}")
print("Done.")
