"""
Fix remaining duplicate migration records in queenscollege for teachers app.
"""
import sys
import os
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
import django
django.setup()

from django.db import connection

schemas_to_fix = ['queenscollege', 'GirlsModel', 'sunshinecriddlecare', 'pentecostprimary', 'tarbiat', 'public']

for schema in schemas_to_fix:
    connection.set_schema(schema)
    with connection.cursor() as c:
        c.execute("SELECT id, app, name FROM django_migrations ORDER BY app, name, id")
        rows = c.fetchall()

    # Find duplicates
    seen = {}
    to_delete = []
    for row_id, app, name in rows:
        key = (app, name)
        if key in seen:
            to_delete.append(row_id)
        else:
            seen[key] = row_id

    if to_delete:
        print(f'{schema}: deleting {len(to_delete)} duplicate record(s)')
        with connection.cursor() as c:
            for row_id in to_delete:
                c.execute("DELETE FROM django_migrations WHERE id = %s", [row_id])
        connection.commit()
        print(f'  done.')
    else:
        print(f'{schema}: no duplicates found')

print('All done.')
