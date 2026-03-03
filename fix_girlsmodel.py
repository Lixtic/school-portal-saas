"""
Fix pending migrations for the GirlsModel tenant.

Root cause: academics_learnermemory table was created outside the migration  
system. migrate_schemas keeps failing on 0020 (table already exists), which
blocks 0021 and students.0007 from ever being applied.

Run: python fix_girlsmodel.py
"""
import os, sys, django
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

from django.db import connection

SCHEMA = 'GirlsModel'
NOW = datetime.now(timezone.utc)


def col_exists(cur, table, col):
    cur.execute("SELECT 1 FROM information_schema.columns WHERE table_schema=%s AND table_name=%s AND column_name=%s",
                [SCHEMA, table, col])
    return cur.fetchone() is not None

def tbl_exists(cur, table):
    cur.execute("SELECT 1 FROM information_schema.tables WHERE table_schema=%s AND table_name=%s",
                [SCHEMA, table])
    return cur.fetchone() is not None

def mig_recorded(cur, app, name):
    cur.execute(f'SELECT 1 FROM "{SCHEMA}".django_migrations WHERE app=%s AND name=%s', [app, name])
    return cur.fetchone() is not None

def record(cur, app, name):
    cur.execute(f'INSERT INTO "{SCHEMA}".django_migrations (app,name,applied) VALUES (%s,%s,%s)', [app, name, NOW])
    print(f"  ✅ Recorded {app}.{name}")


print(f"\n{'='*60}\nFixing migrations for: {SCHEMA}\n{'='*60}")

with connection.cursor() as c:

    # 1. Fake 0020_learner_memory (table already exists physically)
    print("\n[1/3] Faking academics.0020_learner_memory")
    if tbl_exists(c, 'academics_learnermemory'):
        print("  Table exists (orphaned). Marking as applied...")
        if not mig_recorded(c, 'academics', '0020_learner_memory'):
            record(c, 'academics', '0020_learner_memory')
        else:
            print("  ⏭  Already recorded")
    else:
        print("  Table doesn't exist — creating it too")
        c.execute(f"""
            CREATE TABLE "{SCHEMA}".academics_learnermemory (
                id bigserial PRIMARY KEY,
                student_id integer NOT NULL REFERENCES "{SCHEMA}".accounts_user(id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED,
                subject character varying(200) NOT NULL DEFAULT '',
                key_points text NOT NULL DEFAULT '',
                misconceptions text NOT NULL DEFAULT '',
                created_at timestamptz NOT NULL DEFAULT now(),
                updated_at timestamptz NOT NULL DEFAULT now()
            )
        """)
        if not mig_recorded(c, 'academics', '0020_learner_memory'):
            record(c, 'academics', '0020_learner_memory')

    # 2. Apply 0021_studygrouproom_studygroupmessage
    print("\n[2/3] Applying academics.0021")

    if not tbl_exists(c, 'academics_studygrouproom'):
        print("  Creating academics_studygrouproom...")
        c.execute(f"""
            CREATE TABLE "{SCHEMA}".academics_studygrouproom (
                id bigserial PRIMARY KEY,
                name character varying(200) NOT NULL,
                is_global boolean NOT NULL DEFAULT false,
                created_at timestamptz NOT NULL DEFAULT now(),
                student_class_id bigint REFERENCES "{SCHEMA}".academics_class(id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED
            )
        """)
        print("  ✅ Created academics_studygrouproom")
    else:
        print("  ⏭  academics_studygrouproom already exists")

    if not tbl_exists(c, 'academics_studygroupmessage'):
        print("  Creating academics_studygroupmessage...")
        c.execute(f"""
            CREATE TABLE "{SCHEMA}".academics_studygroupmessage (
                id bigserial PRIMARY KEY,
                content text NOT NULL,
                is_aura boolean NOT NULL DEFAULT false,
                is_battle_question boolean NOT NULL DEFAULT false,
                battle_answered boolean NOT NULL DEFAULT false,
                battle_answer character varying(255),
                created_at timestamptz NOT NULL DEFAULT now(),
                battle_winner_id integer REFERENCES "{SCHEMA}".accounts_user(id) ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED,
                room_id bigint NOT NULL REFERENCES "{SCHEMA}".academics_studygrouproom(id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED,
                sender_id integer REFERENCES "{SCHEMA}".accounts_user(id) ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED
            )
        """)
        print("  ✅ Created academics_studygroupmessage")
    else:
        print("  ⏭  academics_studygroupmessage already exists")

    if not mig_recorded(c, 'academics', '0021_studygrouproom_studygroupmessage'):
        record(c, 'academics', '0021_studygrouproom_studygroupmessage')
    else:
        print("  ⏭  0021 already recorded")

    # 3. Apply students.0007
    print("\n[3/3] Applying students.0007")

    if not col_exists(c, 'students_student', 'preferred_language'):
        c.execute(f'ALTER TABLE "{SCHEMA}".students_student ADD COLUMN preferred_language varchar(20) NOT NULL DEFAULT \'english\'')
        print("  ✅ Added preferred_language")
    else:
        print("  ⏭  preferred_language already exists")

    if not col_exists(c, 'students_student', 'aura_notes'):
        c.execute(f'ALTER TABLE "{SCHEMA}".students_student ADD COLUMN aura_notes text NOT NULL DEFAULT \'\'')
        print("  ✅ Added aura_notes")
    else:
        print("  ⏭  aura_notes already exists")

    if not mig_recorded(c, 'students', '0007_add_preferred_language_and_aura_notes'):
        record(c, 'students', '0007_add_preferred_language_and_aura_notes')
    else:
        print("  ⏭  0007 already recorded")

    # Verification
    print("\n[✓] Result")
    ok = all([
        col_exists(c, 'students_student', 'preferred_language'),
        col_exists(c, 'students_student', 'aura_notes'),
        tbl_exists(c, 'academics_studygrouproom'),
        tbl_exists(c, 'academics_studygroupmessage'),
        mig_recorded(c, 'academics', '0020_learner_memory'),
        mig_recorded(c, 'academics', '0021_studygrouproom_studygroupmessage'),
        mig_recorded(c, 'students', '0007_add_preferred_language_and_aura_notes'),
    ])
    if ok:
        print(f"  ✅ SUCCESS — {SCHEMA} is fully up to date. ISE should be resolved.")
    else:
        print(f"  ❌ Something is still missing — check output above")

print(f"\n{'='*60}\n")
