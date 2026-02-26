import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')

import django
django.setup()

from django.db import connection
from tenants.models import School

schools = list(School.objects.values_list('schema_name', flat=True))
print('Schemas:', schools)

for schema in schools:
    connection.set_schema(schema)
    with connection.cursor() as cur:
        cur.execute(
            "SELECT EXISTS(SELECT 1 FROM information_schema.tables "
            "WHERE table_schema=%s AND table_name='communication_conversation')",
            [schema]
        )
        table_exists = cur.fetchone()[0]
        cur.execute(
            "SELECT name FROM django_migrations WHERE app='communication' ORDER BY name"
        )
        rows = [r[0] for r in cur.fetchall()]
    print(f'{schema}: table_exists={table_exists}, comm_migrations={rows}')
