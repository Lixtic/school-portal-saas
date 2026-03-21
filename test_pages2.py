"""Test multiple pages after login - write output to file."""
import os, sys, logging
logging.disable(logging.CRITICAL)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
import django; django.setup()

from django.test import Client

results = []
client = Client(raise_request_exception=False)

resp = client.post('/GirlsModel/login/', {'username': 'admin', 'password': 'testpass123'}, follow=False)
results.append(f"Login: {resp.status_code} -> {resp.get('Location', 'no-redirect')}")
results.append(f"Cookies: {list(client.cookies.keys())}")

pages = [
    ('/GirlsModel/students/', 'students'),
    ('/GirlsModel/teachers/', 'teachers'),
    ('/GirlsModel/finance/', 'finance'),
    ('/GirlsModel/academics/timetable/', 'timetable'),
    ('/GirlsModel/accounts/analytics/', 'analytics'),
    ('/GirlsModel/students/at-risk/', 'at_risk'),
    ('/GirlsModel/announcements/', 'announcements'),
    ('/GirlsModel/accounts/users/', 'manage_users'),
]

for url, name in pages:
    try:
        r = client.get(url, follow=False)
        loc = r.get('Location', 'OK-loaded')
        results.append(f"{name}: status={r.status_code} loc={loc}")
    except Exception as e:
        results.append(f"{name}: EXCEPTION {type(e).__name__}: {str(e)[:200]}")

with open('test_results.txt', 'w') as f:
    f.write('\n'.join(results) + '\n')
