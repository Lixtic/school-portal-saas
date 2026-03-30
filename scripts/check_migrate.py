import os, sys, django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'school_system.settings'
django.setup()

from django.db import connection
from tenants.models import School

tenants = School.objects.exclude(schema_name='public')
for t in tenants:
    print(f'Schema: {t.schema_name}')
    connection.set_schema(t.schema_name)
    cursor = connection.cursor()
    cursor.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name='teachers_teacheraddon' AND column_name='trial_days' "
        "AND table_schema=%s",
        [t.schema_name]
    )
    row = cursor.fetchone()
    print(f'  trial_days exists: {bool(row)}')
connection.set_schema('public')
