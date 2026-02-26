"""
Test that TenantsConfig.ready() actually patches the post_migrate handlers.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
import django
django.setup()

from django.db.models.signals import post_migrate
from django.contrib.contenttypes.management import create_contenttypes
from django.contrib.auth.management import create_permissions

print('post_migrate receivers:')
for receiver in post_migrate.receivers:
    lookup_key, receiver_fn = receiver
    # Try to get function name
    fn = receiver_fn()  # weakref
    if fn:
        name = getattr(fn, '__name__', repr(fn))
        module = getattr(fn, '__module__', '?')
        print(f'  {lookup_key[0]} -> {module}.{name}')
    else:
        print(f'  {lookup_key[0]} -> (dead weakref)')

print()
print(f'create_contenttypes is still connected: {bool([r for r in post_migrate.receivers if r[1]() is create_contenttypes])}')
print(f'create_permissions is still connected: {bool([r for r in post_migrate.receivers if r[1]() is create_permissions])}')
