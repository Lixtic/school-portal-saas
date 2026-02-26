"""Check communication content types and permissions in each schema."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
import django
django.setup()

from django.db import connection
from tenants.models import School

schemas = list(School.objects.values_list('schema_name', flat=True))

for schema in schemas:
    connection.set_schema(schema)
    with connection.cursor() as c:
        c.execute(
            "SELECT id, app_label, model FROM django_content_type "
            "WHERE app_label IN ('communication', 'homework') ORDER BY id"
        )
        cts = c.fetchall()
    
    with connection.cursor() as c:
        ct_ids = [r[0] for r in cts]
        if ct_ids:
            placeholders = ','.join(['%s'] * len(ct_ids))
            c.execute(
                f"SELECT content_type_id, COUNT(*) FROM auth_permission "
                f"WHERE content_type_id IN ({placeholders}) "
                f"GROUP BY content_type_id",
                ct_ids
            )
            perms = dict(c.fetchall())
        else:
            perms = {}
    
    print(f'{schema}:')
    for ct_id, app, model in cts:
        perm_cnt = perms.get(ct_id, 0)
        print(f'  ct_id={ct_id} {app}.{model} -> {perm_cnt} permissions')
    if not cts:
        print('  (no communication/homework content types)')
