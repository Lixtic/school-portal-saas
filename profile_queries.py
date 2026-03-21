"""Count DB queries per view to identify performance issues."""
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')

import django
django.setup()

from django_tenants.utils import schema_context
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from django.db import connection, reset_queries
from django.conf import settings

settings.DEBUG = True  # Enable query logging

User = get_user_model()

SCHEMA = 'GirlsModel'

def count_queries_for_view(view_func, url, schema_name=SCHEMA):
    """Count DB queries for a view using Django test client."""
    from django.test import Client
    from django.contrib.sessions.backends.signed_cookies import SessionStore
    
    with schema_context(schema_name):
        try:
            user = User.objects.get(username='admin')
        except User.DoesNotExist:
            print(f"No admin user in {schema_name}")
            return
    
    client = Client()
    
    # Set the tenant for session
    with schema_context(schema_name):
        client.force_login(user)
    
    # Patch the tenant
    from unittest.mock import patch, MagicMock
    from tenants.models import School
    
    with schema_context(schema_name):
        try:
            tenant = School.objects.get(schema_name=schema_name)
        except School.DoesNotExist:
            print(f"No tenant found for schema {schema_name}")
            return
    
    # Simulate a tenant request
    reset_queries()
    
    response = client.get(url, SERVER_NAME='testserver')
    
    queries = connection.queries
    print(f"\n=== {url} ===")
    print(f"  Status: {response.status_code}")
    if hasattr(response, 'url'):
        print(f"  Redirect: {response.url}")
    print(f"  Total queries: {len(queries)}")
    
    # Show top slowest queries
    if queries:
        sorted_q = sorted(queries, key=lambda q: float(q.get('time', 0)), reverse=True)
        print("  Top 5 slowest queries (in-process, so time shows CPU not network):")
        for i, q in enumerate(sorted_q[:5]):
            sql = q['sql'][:100].replace('\n', ' ')
            print(f"    {i+1}. [{q.get('time','?')}s] {sql}...")
        
        # Check for repeated queries
        seen = {}
        for q in queries:
            sql = q['sql'][:80]
            seen[sql] = seen.get(sql, 0) + 1
        repeated = {k: v for k, v in seen.items() if v > 1}
        if repeated:
            print(f"  REPEATED queries ({len(repeated)} patterns):")
            for sql, count in list(repeated.items())[:5]:
                print(f"    x{count}: {sql[:80]}...")

# Test different views
views_to_test = [
    f'/{SCHEMA}/dashboard/',
    f'/{SCHEMA}/students/',
    f'/{SCHEMA}/teachers/',
    f'/{SCHEMA}/finance/',
]

for url in views_to_test:
    count_queries_for_view(None, url)
