release: python manage.py migrate_schemas --shared && python manage.py migrate_schemas
web: gunicorn school_system.wsgi --log-file -