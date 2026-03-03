import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'school_system.settings'
django.setup()
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'GirlsModel'
        AND table_name = 'students_student'
        AND column_name IN ('preferred_language', 'aura_notes')
        ORDER BY column_name
    """)
    cols = cursor.fetchall()
    print('New columns in GirlsModel.students_student:', [c[0] for c in cols])
    
    cursor.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'GirlsModel'
        AND table_name IN ('academics_learnermemory', 'academics_studygrouproom')
        ORDER BY table_name
    """)
    tables = cursor.fetchall()
    print('New tables in GirlsModel:', [t[0] for t in tables])

    # Check django_migrations table for the pending ones
    cursor.execute("""
        SELECT app, name FROM "GirlsModel".django_migrations
        WHERE app IN ('academics', 'students')
        AND name IN ('0020_learner_memory', '0021_studygrouproom_studygroupmessage', '0007_add_preferred_language_and_aura_notes')
        ORDER BY app, name
    """)
    applied = cursor.fetchall()
    print('Applied in GirlsModel.django_migrations:', applied)
