"""
One-shot script: add the `transition` column to every tenant schema that is missing it.
"""
import os, sys, django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

from django.db import connection
from django_tenants.utils import schema_context
from tenants.models import School

tenants = list(School.objects.exclude(schema_name='public'))
print(f"Found {len(tenants)} tenant(s): {[t.schema_name for t in tenants]}\n")

for tenant in tenants:
    schema = tenant.schema_name
    with schema_context(schema):
        with connection.cursor() as cur:
            cur.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = %s AND table_name = 'teachers_presentation' "
                "AND column_name = 'transition'",
                [schema],
            )
            if cur.fetchone():
                print(f"[{schema}]  transition column already exists — skipping.")
                continue

            print(f"[{schema}]  Adding transition column...")
            cur.execute(
                "ALTER TABLE teachers_presentation "
                "ADD COLUMN IF NOT EXISTS transition VARCHAR(20) NOT NULL DEFAULT 'slide'"
            )
            cur.execute(
                "INSERT INTO django_migrations (app, name, applied) "
                "VALUES ('teachers', '0013_presentation_transition', NOW()) "
                "ON CONFLICT DO NOTHING"
            )
            print(f"[{schema}]  Done.")

print("\nAll tenants processed.")
