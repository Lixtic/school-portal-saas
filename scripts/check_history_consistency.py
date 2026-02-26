"""
Check migration consistency for queenscollege — find any squashed/out-of-order
or missing parent records.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
import django
django.setup()

from django.db import connection
from django.db.migrations.loader import MigrationLoader

schemas = ['queenscollege', 'pentecostprimary', 'tarbiat']

for schema in schemas:
    connection.set_schema(schema)
    print(f'\n{schema}:')
    try:
        loader = MigrationLoader(connection)
        loader.check_consistent_history(connection)
        print('  consistent_history: OK')
    except Exception as e:
        print(f'  consistent_history ERROR: {e}')

    with connection.cursor() as c:
        c.execute(
            "SELECT app, name FROM django_migrations ORDER BY app, id"
        )
        rows = c.fetchall()

    # Show duplicates
    from collections import Counter
    counts = Counter((app, name) for app, name in rows)
    dupes = [(app, name, cnt) for (app, name), cnt in counts.items() if cnt > 1]
    if dupes:
        print(f'  DUPLICATES: {dupes}')
    else:
        print(f'  No duplicates')

    # Show total counts per app
    app_counts = Counter(app for app, name in rows)
    for app, cnt in sorted(app_counts.items()):
        print(f'    {app}: {cnt} migration(s)')
