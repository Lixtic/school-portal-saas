"""Test real login flow end-to-end."""
import os, sys, logging
logging.disable(logging.CRITICAL)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
import django
django.setup()

from django.test import Client

client = Client(raise_request_exception=True)

# Step 1: GET login page to get CSRF token
resp = client.get('/GirlsModel/login/')
sys.stdout.write(f"Step 1 - Login page GET: {resp.status_code}\n")

# Step 2: POST credentials 
resp2 = client.post('/GirlsModel/login/', {
    'username': 'admin',
    'password': 'testpass123',
}, follow=False)
sys.stdout.write(f"Step 2 - Login POST: {resp2.status_code}\n")
sys.stdout.write(f"Step 2 - Redirect to: {resp2.get('Location', 'NO REDIRECT')}\n")
sys.stdout.write(f"Step 2 - Cookies set: {list(client.cookies.keys())}\n")

if '_sp_session' in client.cookies:
    cookie = client.cookies['_sp_session']
    sys.stdout.write(f"Step 2 - Session cookie value length: {len(cookie.value)}\n")
    sys.stdout.write(f"Step 2 - Cookie path: {cookie.get('path', 'not set')}\n")
    sys.stdout.write(f"Step 2 - Cookie secure: {cookie.get('secure', 'not set')}\n")
else:
    sys.stdout.write("Step 2 - NO _sp_session COOKIE SET! This is the bug.\n")

# Step 3: Access dashboard
resp3 = client.get('/GirlsModel/dashboard/', follow=False)
sys.stdout.write(f"Step 3 - Dashboard GET: {resp3.status_code}\n")
sys.stdout.write(f"Step 3 - Location: {resp3.get('Location', 'No redirect - page loaded')}\n")

# Step 4: Access students (should show 200 if logged in)
resp4 = client.get('/GirlsModel/students/', follow=False)
sys.stdout.write(f"Step 4 - Students GET: {resp4.status_code}\n")
sys.stdout.write(f"Step 4 - Location: {resp4.get('Location', 'No redirect - page loaded')}\n")
sys.stdout.flush()
