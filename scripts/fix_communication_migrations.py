"""
Fix communication migration state across all schemas:
1. GirlsModel - has table but 0002 not recorded -> fake-insert 0002 record
2. public     - duplicate migration records -> deduplicate
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')

import django
django.setup()

from django.db import connection
from tenants.models import School

schools = list(School.objects.values_list('schema_name', flat=True))

for schema in schools:
    connection.set_schema(schema)
    with connection.cursor() as cur:
        # --- 1. Deduplicate django_migrations ---
        cur.execute(
            "SELECT app, name, COUNT(*) c FROM django_migrations "
            "GROUP BY app, name HAVING COUNT(*) > 1"
        )
        dupes = cur.fetchall()
        if dupes:
            print(f'{schema}: deduplicating {len(dupes)} migration(s) ...')
            for app, name, cnt in dupes:
                # Keep one, delete extras
                cur.execute(
                    "DELETE FROM django_migrations WHERE id IN ("
                    "  SELECT id FROM django_migrations "
                    "  WHERE app=%s AND name=%s "
                    "  ORDER BY id DESC "
                    "  LIMIT %s"
                    ")",
                    [app, name, cnt - 1],
                )
            connection.commit()
            print(f'  done.')

        # --- 2. Fake-insert missing 0002 for GirlsModel ---
        if schema == 'GirlsModel':
            cur.execute(
                "SELECT 1 FROM django_migrations "
                "WHERE app='communication' AND name='0002_conversation_message'"
            )
            if not cur.fetchone():
                print(f'{schema}: inserting fake 0002_conversation_message record ...')
                cur.execute(
                    "INSERT INTO django_migrations (app, name, applied) "
                    "VALUES ('communication', '0002_conversation_message', NOW())"
                )
                connection.commit()
                print(f'  done.')

print('All done.')
