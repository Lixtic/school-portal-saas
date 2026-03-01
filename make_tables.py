import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings'); django.setup(); from django.db import connection; 
from django_tenants.utils import schema_context
with schema_context('school1'):
    with connection.cursor() as cursor:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS academics_studygrouproom (
                id SERIAL PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                is_global BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                student_class_id INTEGER UNIQUE REFERENCES academics_class(id) ON DELETE CASCADE
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS academics_studygroupmessage (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                is_aura BOOLEAN NOT NULL DEFAULT FALSE,
                is_battle_question BOOLEAN NOT NULL DEFAULT FALSE,
                battle_answered BOOLEAN NOT NULL DEFAULT FALSE,
                battle_answer VARCHAR(255),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                room_id INTEGER NOT NULL REFERENCES academics_studygrouproom(id) ON DELETE CASCADE,
                sender_id INTEGER REFERENCES accounts_user(id) ON DELETE SET NULL,
                battle_winner_id INTEGER REFERENCES accounts_user(id) ON DELETE SET NULL
            )
        ''')
        print('Tables created.')

