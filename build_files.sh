#!/bin/bash
echo "Building project..."
python3 -m pip install -r requirements.txt

echo "Collect Static..."
python3 manage.py collectstatic --noinput --clear

echo "Running Migrations..."
# python3 manage.py makemigrations # Disabled: Should be committed
python3 manage.py migrate_schemas --shared
python3 manage.py migrate_schemas
python3 scripts/setup_tenants.py
# python3 manage.py populate_curriculum
# python3 scripts/fix_notification_table.py
