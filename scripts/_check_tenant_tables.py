"""Quick check: which tenants have the teachers_teacheraddon table?"""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.db import connection
from tenants.models import School

for t in School.objects.exclude(schema_name='public'):
    connection.set_tenant(t)
    with connection.cursor() as c:
        c.execute(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema=%s AND table_name='teachers_teacheraddon'",
            [t.schema_name],
        )
        exists = c.fetchone()[0] > 0
        print(f"{t.schema_name}: teachers_teacheraddon exists = {exists}")
