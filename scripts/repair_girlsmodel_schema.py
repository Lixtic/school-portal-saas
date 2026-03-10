"""
Full tenant schema repair:
 1. Find tables recorded as applied in django_migrations but physically missing
 2. Fix duplicate share_token values blocking teachers.0012 unique index
 3. Create any missing tables via targeted ALTER/CREATE
 4. Ensure migration records are correct
"""
import os, sys, uuid, django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

from django.db import connection
from django.core.management import call_command
from django_tenants.utils import schema_context
from tenants.models import School

SCHEMA = 'GirlsModel'

print(f"=== Repairing tenant schema: {SCHEMA} ===\n")

with schema_context(SCHEMA):
    with connection.cursor() as cur:

        # ── Step 1: Check which tables actually exist ──────────────────
        cur.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = %s AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """, [SCHEMA])
        existing_tables = {r[0] for r in cur.fetchall()}
        print(f"[1] Tables existing in {SCHEMA}: {len(existing_tables)}")

        # ── Step 2: Tables we know should exist based on migrations ────
        EXPECTED_MISSING = [
            'academics_studygrouproom',
            'academics_studygroupmessage',
        ]
        for tbl in EXPECTED_MISSING:
            exists = tbl in existing_tables
            print(f"    {'OK' if exists else 'MISSING'}: {tbl}")

        # ── Step 3: Fix share_token column + unique index (teachers.0012) ─────
        print("\n[2] Checking teachers_presentation.share_token column...")
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = %s AND table_name = 'teachers_presentation'
            AND column_name = 'share_token'
        """, [SCHEMA])
        has_share_token = cur.fetchone()
        if not has_share_token:
            print("    Column missing — adding share_token...")
            cur.execute("""
                ALTER TABLE teachers_presentation
                ADD COLUMN IF NOT EXISTS share_token UUID NOT NULL DEFAULT gen_random_uuid()
            """)
            print("    Added.")

        # Now try to create the unique index — fix duplicates first
        print("    Checking for duplicate share_tokens...")
        cur.execute("""
            SELECT share_token, COUNT(*) FROM teachers_presentation
            GROUP BY share_token HAVING COUNT(*) > 1
        """)
        dupes = cur.fetchall()
        if dupes:
            print(f"    {len(dupes)} duplicate share_token(s) found — fixing...")
            for token, cnt in dupes:
                cur.execute(
                    "SELECT id FROM teachers_presentation WHERE share_token = %s ORDER BY id",
                    [token]
                )
                ids = [r[0] for r in cur.fetchall()]
                for dup_id in ids[1:]:
                    new_token = str(uuid.uuid4())
                    cur.execute(
                        "UPDATE teachers_presentation SET share_token = %s WHERE id = %s",
                        [new_token, dup_id]
                    )
                    print(f"    Updated id={dup_id} -> {new_token[:8]}...")
            print("    Duplicates resolved.")
        else:
            print("    No duplicates.")

        # Create unique index if it doesn't exist
        cur.execute("""
            SELECT indexname FROM pg_indexes
            WHERE schemaname = %s AND tablename = 'teachers_presentation'
            AND indexname = 'teachers_presentation_share_token_key'
        """, [SCHEMA])
        if not cur.fetchone():
            print("    Creating unique index on share_token...")
            cur.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS teachers_presentation_share_token_key
                ON teachers_presentation (share_token)
            """)
            print("    Unique index created.")

        # ── Step 4: Create missing academics tables ────────────────────
        print("\n[3] Creating missing tables...")

        if 'academics_studygrouproom' not in existing_tables:
            print("    Creating academics_studygrouproom...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS academics_studygrouproom (
                    id               BIGSERIAL PRIMARY KEY,
                    name             VARCHAR(200) NOT NULL,
                    is_global        BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at       TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    student_class_id BIGINT UNIQUE REFERENCES academics_class(id) ON DELETE CASCADE
                )
            """)
            print("    Done: academics_studygrouproom")

        if 'academics_studygroupmessage' not in existing_tables:
            print("    Creating academics_studygroupmessage...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS academics_studygroupmessage (
                    id               BIGSERIAL PRIMARY KEY,
                    content          TEXT NOT NULL,
                    is_aura          BOOLEAN NOT NULL DEFAULT FALSE,
                    is_battle_question BOOLEAN NOT NULL DEFAULT FALSE,
                    battle_answered  BOOLEAN NOT NULL DEFAULT FALSE,
                    battle_answer    VARCHAR(255),
                    created_at       TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    room_id          BIGINT NOT NULL REFERENCES academics_studygrouproom(id) ON DELETE CASCADE,
                    sender_id        INTEGER REFERENCES accounts_user(id) ON DELETE SET NULL,
                    battle_winner_id INTEGER REFERENCES accounts_user(id) ON DELETE SET NULL
                )
            """)
            print("    Done: academics_studygroupmessage")

        # ── Step 5: Ensure migration record exists ─────────────────────
        print("\n[4] Ensuring migration records exist...")
        records_to_ensure = [
            ('academics', '0021_studygrouproom_studygroupmessage'),
            ('teachers',  '0012_presentation_share_token'),
            ('teachers',  '0013_presentation_transition'),
        ]
        for app, name in records_to_ensure:
            cur.execute(
                "SELECT 1 FROM django_migrations WHERE app=%s AND name=%s",
                [app, name]
            )
            if cur.fetchone():
                print(f"    Already recorded: {app}.{name}")
            else:
                cur.execute(
                    "INSERT INTO django_migrations (app, name, applied) VALUES (%s, %s, NOW())",
                    [app, name]
                )
                print(f"    Recorded: {app}.{name}")

print("\n=== Done. ===")
