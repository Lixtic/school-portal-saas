"""
Check what permissions are MISSING in queenscollege for communication app
compared to other schemas.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
import django
django.setup()

from django.db import connection
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission

schemas = ['sunshinecriddlecare', 'queenscollege']

for schema in schemas:
    connection.set_schema(schema)
    ContentType.objects.clear_cache()
    perms = list(
        Permission.objects.using('default')
        .filter(content_type__app_label='communication')
        .values_list('content_type__model', 'codename')
        .order_by('content_type__model', 'codename')
    )
    print(f'\n{schema}: {len(perms)} permissions')
    for model, codename in perms:
        print(f'  {model}.{codename}')
