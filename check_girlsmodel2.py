import os, sys, django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()
from django.db import connection

SCHEMA = 'GirlsModel'

with connection.cursor() as cursor:
    cursor.execute(f"""
        SELECT app, name, applied FROM "{SCHEMA}".django_migrations
        WHERE app IN ('academics', 'students')
        ORDER BY app, applied
    """)
    rows = cursor.fetchall()
    print(f"Current django_migrations in {SCHEMA} for academics/students:")
    for r in rows:
        print(f"  {r[0]}.{r[1]} (applied: {r[2]})")
    
    # Also list all tables in GirlsModel
    cursor.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = %s
        AND table_name LIKE 'academics_%%'
        ORDER BY table_name
    """, [SCHEMA])
    tables = [r[0] for r in cursor.fetchall()]
    print(f"\nAll academics_* tables in {SCHEMA}:")
    for t in tables:
        print(f"  {t}")
