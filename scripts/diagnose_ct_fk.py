"""
Diagnose the FK violation: FK points to content_type_id=54 which doesn't exist.
Find which schema's auth_permission has orphaned content_type references.
"""
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
        # Max content type ID
        c.execute("SELECT MAX(id) FROM django_content_type")
        max_ct = c.fetchone()[0]
        
        # Any auth_permissions pointing to non-existent content types?
        c.execute("""
            SELECT p.content_type_id, COUNT(*) 
            FROM auth_permission p
            LEFT JOIN django_content_type ct ON p.content_type_id = ct.id
            WHERE ct.id IS NULL
            GROUP BY p.content_type_id
        """)
        orphans = c.fetchall()
        
        # Check for content type ID 54 specifically
        c.execute("SELECT id, app_label, model FROM django_content_type WHERE id = 54")
        ct54 = c.fetchone()
        
    print(f'{schema}:')
    print(f'  max content_type id: {max_ct}')
    print(f'  orphaned permissions (ct_id -> count): {orphans}')
    print(f'  content_type id=54: {ct54}')
