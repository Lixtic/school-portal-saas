"""
Fix stale content types AND duplicate auth_permission rows across all schemas.

Two distinct FK/unique constraint violations can occur during migrate_schemas:

  (A) MISSING content type:
      "insert or update on table auth_permission violates foreign key constraint
       DETAIL: Key (content_type_id)=(54) not present in django_content_type"
      Caused by stale content type rows left over when apps move between
      SHARED_APPS and TENANT_APPS.
      Fix: delete content type rows whose (app_label, model) pair no longer
           matches any installed app.

  (B) DUPLICATE permission:
      "duplicate key value violates unique constraint
       auth_permission_content_type_id_codename_01ab375a_uniq
       DETAIL: Key (content_type_id, codename)=(57, add_studentachievement) already exists"
      Caused by auth_permission rows already existing when post_migrate fires
      again (e.g. after a Vercel re-deployment on an unchanged DB).
      Fix: delete duplicate rows keeping only MIN(id) for each (ct, codename).

Both are fixed here before migrate_schemas runs in build_files.sh.
"""
import os
import sys
import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

from django.db import connection
from django_tenants.utils import schema_context, get_public_schema_name
from django.apps import apps as django_apps


def _get_installed_ct_pairs():
    """Return a set of (app_label, model) for all installed models."""
    return {
        (model._meta.app_label, model._meta.model_name)
        for model in django_apps.get_models()
    }


def _remove_stale_contenttypes(schema_name, installed_pairs):
    """Delete content type rows whose app+model no longer exists."""
    from django.contrib.contenttypes.models import ContentType
    stale = ContentType.objects.exclude(
        app_label__in=[p[0] for p in installed_pairs]
    ).filter(
        # Only delete if BOTH app_label AND model are stale together
        # (avoids deleting valid cts whose app_label exists but model differs)
    )
    # More precise: find rows where the (app_label, model) pair isn't installed
    stale_ids = [
        ct.id
        for ct in ContentType.objects.all()
        if (ct.app_label, ct.model) not in installed_pairs
    ]
    if stale_ids:
        ContentType.objects.filter(id__in=stale_ids).delete()
        print(f"  ✓ {schema_name}: deleted {len(stale_ids)} stale content type(s)")


def _dedup_permissions(schema_name):
    """Keep only MIN(id) for each (content_type_id, codename) pair."""
    with connection.cursor() as cursor:
        cursor.execute(f'SET search_path TO "{schema_name}", public')
        cursor.execute("""
            DELETE FROM auth_permission
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM auth_permission
                GROUP BY content_type_id, codename
            )
        """)
        deleted = cursor.rowcount
    if deleted >= 0:
        print(f"  ✓ {schema_name}: removed {deleted} duplicate auth_permission row(s)")


def fix_schema(schema_name, installed_pairs):
    with schema_context(schema_name):
        try:
            _remove_stale_contenttypes(schema_name, installed_pairs)
        except Exception as exc:
            print(f"  ⚠ {schema_name}: remove_stale_contenttypes: {exc}")

        try:
            _dedup_permissions(schema_name)
        except Exception as exc:
            print(f"  ⚠ {schema_name}: dedup_permissions: {exc}")


def main():
    from tenants.models import School

    print("=== Fixing content types and permissions ===")
    installed_pairs = _get_installed_ct_pairs()

    fix_schema(get_public_schema_name(), installed_pairs)

    for school in School.objects.exclude(schema_name=get_public_schema_name()):
        fix_schema(school.schema_name, installed_pairs)

    print("=== Done ===")


if __name__ == '__main__':
    main()
