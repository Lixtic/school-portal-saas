import os; os.environ['DJANGO_SETTINGS_MODULE']='school_system.settings'
import django; django.setup()
from django.conf import settings
db = settings.DATABASES['default']
print('ATOMIC_REQUESTS:', db.get('ATOMIC_REQUESTS', False))
print('AUTOCOMMIT:', db.get('AUTOCOMMIT', True))

settings.DEBUG = True
from django_tenants.utils import schema_context
from django.test import Client
from django.contrib.auth import get_user_model
from django.db import connection, reset_queries
User = get_user_model()

with schema_context('GirlsModel'):
    admin = User.objects.get(username='admin')

client = Client(raise_request_exception=True)
with schema_context('GirlsModel'):
    client.force_login(admin)

reset_queries()
resp = client.get('/GirlsModel/login/')
qs = connection.queries
print(f'Login GET: status={resp.status_code}, queries={len(qs)}')
set_calls = sum(1 for q in qs if 'SET search_path' in q.get('sql',''))
print(f'  SET search_path calls: {set_calls}')
for q in qs:
    sql = q['sql'][:80].replace('\n', ' ')
    print(f'  [{q.get("time","?")}s] {sql}')
