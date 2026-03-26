"""
Rename existing admin users from 'admin' to 'admin_{schema_name}'.

Each tenant currently has an admin user with username='admin'. This script
renames them to 'admin_{schema_name}' (e.g., 'admin_GirlsModel') to ensure
uniqueness across the platform and eliminate cross-tenant session confusion.

Usage:
    python scripts/rename_admin_users.py
    python scripts/rename_admin_users.py --dry-run   # Preview without changes
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')

import django
django.setup()

from django.contrib.auth import get_user_model
from django.db import connection

User = get_user_model()


def rename_admins(dry_run=False):
    from tenants.models import School

    tenants = School.objects.filter(is_active=True).exclude(schema_name='public')
    print(f"Found {tenants.count()} active tenant(s).\n")

    renamed = 0
    skipped = 0
    errors = 0

    for tenant in tenants:
        schema = tenant.schema_name
        new_username = f'admin_{schema}'

        try:
            connection.set_tenant(tenant)

            # Find the old 'admin' user
            try:
                admin_user = User.objects.get(username='admin', user_type='admin')
            except User.DoesNotExist:
                # Maybe already renamed or never created
                existing = User.objects.filter(username=new_username).exists()
                if existing:
                    print(f"  [{schema}] Already has '{new_username}' — skipping")
                else:
                    print(f"  [{schema}] No 'admin' user found — skipping")
                skipped += 1
                continue

            # Check the new username isn't already taken
            if User.objects.filter(username=new_username).exclude(pk=admin_user.pk).exists():
                print(f"  [{schema}] '{new_username}' already taken by another user — skipping")
                skipped += 1
                continue

            old_username = admin_user.username
            if dry_run:
                print(f"  [{schema}] Would rename '{old_username}' → '{new_username}'")
            else:
                admin_user.username = new_username
                admin_user.save(update_fields=['username'])
                print(f"  [{schema}] Renamed '{old_username}' → '{new_username}'")
            renamed += 1

        except Exception as e:
            print(f"  [{schema}] ERROR: {e}")
            errors += 1
        finally:
            connection.set_schema_to_public()

    print(f"\nDone. Renamed: {renamed}, Skipped: {skipped}, Errors: {errors}")
    if dry_run:
        print("(Dry run — no changes were made)")


if __name__ == '__main__':
    dry = '--dry-run' in sys.argv
    rename_admins(dry_run=dry)
