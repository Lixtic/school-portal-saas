"""
Deep dive: for each schema, cross-check what Django migration executor thinks
is pending vs what tables actually exist.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
import django
django.setup()

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from tenants.models import School

COMMUNICATION_TABLES = ['communication_conversation', 'communication_message']

schools = list(School.objects.values_list('schema_name', flat=True))

print("=" * 70)
for schema in schools:
    connection.set_schema(schema)
    with connection.cursor() as c:
        # Migration records
        c.execute(
            "SELECT app, name FROM django_migrations "
            "ORDER BY app, name"
        )
        all_migs = [(r[0], r[1]) for r in c.fetchall()]
        comm_migs = [name for app, name in all_migs if app == 'communication']
        homework_migs = [name for app, name in all_migs if app == 'homework']

        # Tables
        c.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = %s "
            "AND table_name IN ('communication_conversation', 'communication_message', "
            "                   'homework_homework', 'homework_submission')",
            [schema]
        )
        tables = sorted(r[0] for r in c.fetchall())

    # What executor thinks is pending
    executor = MigrationExecutor(connection)
    targets = executor.loader.graph.leaf_nodes()
    plan = executor.migration_plan(targets)
    pending = [f'{m.app_label}.{m.name}' for m, bw in plan]

    print(f"\n{schema}:")
    print(f"  communication migs : {comm_migs}")
    print(f"  homework migs      : {homework_migs}")
    print(f"  tables present     : {tables}")
    print(f"  executor pending   : {pending if pending else '(none)'}")

print("=" * 70)
