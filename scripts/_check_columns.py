"""Check columns in GirlsModel.teachers_teacheraddon"""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.db import connection
from tenants.models import School

for schema in ['sunshinecriddlecare', 'tarbiat', 'GirlsModel']:
    t = School.objects.get(schema_name=schema)
    connection.set_tenant(t)
    with connection.cursor() as c:
        c.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema=%s AND table_name='teachers_teacheraddon' "
            "ORDER BY ordinal_position",
            [schema],
        )
        cols = [r[0] for r in c.fetchall()]
        print(f"{schema}: {cols}")
