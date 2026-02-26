"""Fake-apply communication.0002_conversation_message in GirlsModel schema."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
import django
django.setup()

from django.db import connection
from django.utils import timezone

connection.set_schema('GirlsModel')
with connection.cursor() as c:
    c.execute(
        "SELECT name FROM django_migrations WHERE app='communication' ORDER BY name"
    )
    rows = [r[0] for r in c.fetchall()]
    print('communication migrations in GirlsModel:', rows)

    if '0002_conversation_message' not in rows:
        c.execute(
            "INSERT INTO django_migrations (app, name, applied) VALUES (%s, %s, %s)",
            ['communication', '0002_conversation_message', timezone.now()],
        )
        print('Inserted fake 0002 record.')
    else:
        print('0002 already present — no action needed.')

connection.commit()
print('Done.')
