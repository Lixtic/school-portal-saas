"""Show pending migrations per schema."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
import django
django.setup()

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from tenants.models import School

schools = list(School.objects.values_list('schema_name', flat=True))
# Add public
if 'public' not in schools:
    schools.insert(0, 'public')

for schema in schools:
    connection.set_schema(schema)
    executor = MigrationExecutor(connection)
    targets = executor.loader.graph.leaf_nodes()
    plan = executor.migration_plan(targets)
    if plan:
        print(f'{schema}: PENDING {len(plan)} migration(s):')
        for migration, backwards in plan:
            print(f'  {"<-" if backwards else "->"} {migration.app_label}.{migration.name}')
    else:
        print(f'{schema}: up-to-date')
