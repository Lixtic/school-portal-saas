import os, sys, django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

from django.db import connection
from tenants.models import School

tenant = School.objects.get(schema_name='GirlsModel')
connection.set_tenant(tenant)

with connection.cursor() as c:
    c.execute(
        "SELECT tablename FROM pg_tables WHERE schemaname=%s AND tablename LIKE %s ORDER BY tablename",
        ['GirlsModel', 'announcements%']
    )
    rows = c.fetchall()
    if rows:
        for r in rows:
            print(r[0])
    else:
        print("NO announcements tables found in GirlsModel schema")
