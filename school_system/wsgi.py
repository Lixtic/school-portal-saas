"""
WSGI config for school_system project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')

application = get_wsgi_application()

# --- Vercel Auto-Migration Hook (Improved) ---
try:
    from django.db import connection
    from django.core.management import call_command
    import sys
    
    # Ensure connection is fresh
    connection.ensure_connection()

    # check if table exists using introspection
    db_tables = connection.introspection.table_names()
    
    if 'tenants_school' not in db_tables:
        print(">>> WSGI: 'tenants_school' table not found. Starting initialization...")
        
        # 1. Run Shared Migrations
        print(">>> WSGI: Running migrate_schemas --shared")
        call_command('migrate_schemas', shared=True, interactive=False)
        
        # 2. Setup Tenants
        print(">>> WSGI: Running setup_tenants")
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from scripts.setup_tenants import setup_tenants
        setup_tenants()
        
        print(">>> WSGI: Initialization Complete.")
    else:
        # Check for pending migrations
        # ALWAYS RUN MIGRATIONS ON VERCEL INIT to catch new fields like 'homepage_template'
        print(">>> WSGI: Checking for migrations...")
        try:
             # Run migrations for both shared and tenants to be safe
             call_command('migrate_schemas', interactive=False)
             print(">>> WSGI: Migrations applied successfully.")
        except Exception as mig_e:
             print(f">>> WSGI MIGRATION ERROR: {mig_e}")
             
        # Double check if public tenant exists

        from tenants.models import School
        if not School.objects.filter(schema_name='public').exists():
             print(">>> WSGI: Public tenant missing! Running setup_tenants...")
             sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
             from scripts.setup_tenants import setup_tenants
             setup_tenants()

except Exception as e:
    print(f">>> WSGI INIT ERROR: {e}")
# ------------------------------------------

app = application

