"""Test multiple pages after login."""
import os, sys, logging
logging.disable(logging.CRITICAL)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
import django; django.setup()

from django.test import Client
client = Client(raise_request_exception=False)

resp = client.post('/GirlsModel/login/', {'username': 'admin', 'password': 'testpass123'}, follow=False)
sys.stdout.write(f"Login: {resp.status_code} -> {resp.get('Location', 'no-redirect')}\n")
sys.stdout.write(f"Cookies: {list(client.cookies.keys())}\n")
sys.stdout.flush()

pages = [
    ('/GirlsModel/students/', 'students'),
    ('/GirlsModel/teachers/', 'teachers'),
    ('/GirlsModel/finance/', 'finance'),
    ('/GirlsModel/academics/timetable/', 'timetable'),
    ('/GirlsModel/accounts/analytics/', 'analytics'),
    ('/GirlsModel/students/at-risk/', 'at_risk'),
    ('/GirlsModel/announcements/', 'announcements'),
    ('/GirlsModel/academics/manage-classes/', 'manage_classes'),
    ('/GirlsModel/accounts/users/', 'manage_users'),
]

for url, name in pages:
    try:
        r = client.get(url, follow=False)
        loc = r.get('Location', 'OK-loaded')
        sys.stdout.write(f"{name}: status={r.status_code} loc={loc}\n")
        sys.stdout.flush()
    except Exception as e:
        sys.stdout.write(f"{name}: EXCEPTION {type(e).__name__}: {str(e)[:150]}\n")
        sys.stdout.flush()
