import os, sys, traceback
os.environ['DJANGO_SETTINGS_MODULE'] = 'school_system.settings'

import django
django.setup()

from django_tenants.utils import schema_context
from tenants.models import School

# Find a tenant with setup_complete
target_schema = None
for school in School.objects.exclude(schema_name='public'):
    with schema_context(school.schema_name):
        from academics.models import SchoolInfo as SI
        si = SI.objects.first()
        sc = getattr(si, 'setup_complete', False)
        print(f'{school.schema_name}: setup_complete={sc}')
        if sc:
            target_schema = school.schema_name
            break

if not target_schema:
    # Force setup_complete on first tenant for test
    school = School.objects.exclude(schema_name='public').first()
    if school:
        target_schema = school.schema_name
        with schema_context(target_schema):
            from academics.models import SchoolInfo as SI2
            si2 = SI2.objects.first()
            if si2:
                si2.setup_complete = True
                si2.save()
                print(f'Forced setup_complete on {target_schema}')

if not target_schema:
    print('No tenants found')
    sys.exit(1)

print(f'\nTesting admin dashboard for schema: {target_schema}')

from django.contrib.auth import get_user_model
User = get_user_model()

from django.test import Client
import django.test.utils

with schema_context(target_schema):
    admin = User.objects.filter(user_type='admin').first()
    if not admin:
        print('No admin user in schema')
        sys.exit(1)
    print(f'Admin user: {admin.username}')

c = Client(raise_request_exception=True)
c.force_login(admin)

# Patch the connection schema
from django.db import connection
connection.set_schema(target_schema)

from django.test.utils import override_settings
# Attempt to get dashboard
try:
    with schema_context(target_schema):
        from accounts.views import dashboard
        from django.test import RequestFactory
        rf = RequestFactory()
        req = rf.get(f'/{target_schema}/dashboard/')
        req.user = admin
        req.tenant = School.objects.get(schema_name=target_schema)
        req.META['SCRIPT_NAME'] = f'/{target_schema}'
        connection.set_schema_to_public()
        connection.set_schema(target_schema)
        
        try:
            response = dashboard(req)
            print('Status code:', response.status_code)
        except Exception as e:
            print('ERROR:', type(e).__name__, str(e))
            traceback.print_exc()
except Exception as e:
    print('OUTER ERROR:', type(e).__name__, str(e))
    traceback.print_exc()
