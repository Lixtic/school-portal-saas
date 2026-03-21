"""One-shot session diagnostic script."""
import os, sys, logging
logging.disable(logging.CRITICAL)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')

import django
django.setup()

from django.db import connection
from tenants.models import School
from django.test import Client

school = School.objects.get(schema_name='GirlsModel')
connection.set_tenant(school)

from django.contrib.auth import get_user_model
User = get_user_model()
admin = User.objects.get(username='admin')

print(f"Admin user: {admin.username}, type: {admin.user_type}, active: {admin.is_active}")

client = Client()
client.force_login(admin)

print(f"Cookies after force_login: {list(client.cookies.keys())}")

# Test 1: Access students page
resp = client.get('/GirlsModel/students/', follow=False)
sys.stdout.write(f"Students status: {resp.status_code}, Location: {resp.get('Location', 'OK-loaded')}\n")

# Test 2: Access dashboard
resp2 = client.get('/GirlsModel/dashboard/', follow=False)
sys.stdout.write(f"Dashboard status: {resp2.status_code}, Location: {resp2.get('Location', 'OK-loaded')}\n")

# Test 3: Check what the session looks like
if hasattr(client, 'session'):
    session = client.session
    sys.stdout.write(f"Session keys: {list(session.keys())}\n")
    sys.stdout.write(f"Session auth_user_id: {session.get('_auth_user_id', 'NOT SET')}\n")
