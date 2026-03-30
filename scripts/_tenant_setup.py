"""
Shared tenant-aware setup for standalone scripts.

Usage:
    from _tenant_setup import setup_tenant
    setup_tenant()          # prompts or uses sys.argv[1]
    setup_tenant('GirlsModel')  # explicit schema
"""
import os, sys

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')

import django
django.setup()

from django.db import connection
from tenants.models import School


def setup_tenant(schema_name=None):
    """Switch the DB connection to the given tenant schema.
    Falls back to sys.argv[1] or lists available tenants."""
    if schema_name is None:
        schema_name = sys.argv[1] if len(sys.argv) > 1 else None

    tenants = list(School.objects.exclude(schema_name='public').values_list('schema_name', flat=True))

    if not schema_name:
        print("Available tenants:", ', '.join(tenants))
        print("Usage: python scripts/<script>.py <schema_name>")
        sys.exit(1)

    if schema_name not in tenants:
        print(f"Tenant '{schema_name}' not found. Available: {', '.join(tenants)}")
        sys.exit(1)

    tenant = School.objects.get(schema_name=schema_name)
    connection.set_tenant(tenant)
    print(f"[tenant: {schema_name}]")
    return tenant


def iter_tenants():
    """Yield each non-public tenant after switching the connection."""
    for tenant in School.objects.exclude(schema_name='public'):
        connection.set_tenant(tenant)
        yield tenant
