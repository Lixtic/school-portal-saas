"""Investigate content type 54 in queenscollege."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
import django
django.setup()

from django.db import connection

connection.set_schema('queenscollege')
with connection.cursor() as c:
    c.execute("SELECT id, app_label, model FROM django_content_type ORDER BY id DESC LIMIT 10")
    rows = c.fetchall()
    print('Last 10 content types in queenscollege:')
    for r in rows:
        print(f'  id={r[0]} {r[1]}.{r[2]}')
    
    c.execute("SELECT MAX(id), MIN(id), COUNT(*) FROM django_content_type")
    stats = c.fetchone()
    print(f'\nStats: max={stats[0]}, min={stats[1]}, count={stats[2]}')
    
    # All IDs from 50+
    c.execute("SELECT id, app_label, model FROM django_content_type WHERE id >= 50 ORDER BY id")
    rows = c.fetchall()
    print('\nCTs id>=50:')
    for r in rows:
        print(f'  id={r[0]} {r[1]}.{r[2]}')
    
    # The actual error says id=54 is missing but is referenced
    # Check what permissions exist pointing to id=54
    c.execute("SELECT COUNT(*) FROM auth_permission WHERE content_type_id = 54")
    perms54 = c.fetchone()[0]
    print(f'\nPermissions pointing to ct_id=54: {perms54}')
    
    # Check sequence
    c.execute("SELECT last_value FROM django_content_type_id_seq")
    seq = c.fetchone()[0]
    print(f'Sequence last_value: {seq}')
