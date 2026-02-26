"""
Test the _safe_create_permissions logic against sunshinecriddlecare to
reproduce the FK violation.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
import django
django.setup()

from django.db import connection, DEFAULT_DB_ALIAS, router
from django.db.models.signals import post_migrate
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from django.apps import apps as global_apps

schemas = ['sunshinecriddlecare', 'GirlsModel', 'queenscollege']

for schema in schemas:
    connection.set_schema(schema)
    print(f'\n=== Schema: {schema} ===')
    
    # Simulate what happens when post_migrate fires for communication app
    app_config = global_apps.get_app_config('communication')
    using = 'default'
    
    # Clear cache
    ContentType.objects.clear_cache()
    
    # Get communication content types in this schema
    cts = list(ContentType.objects.using(using).filter(app_label='communication'))
    print(f'  communication CTs in DB: {[(ct.pk, ct.model) for ct in cts]}')
    
    ct_map = {ct.model: ct for ct in cts}
    
    # Get existing permissions
    existing = set(
        Permission.objects.using(using)
        .filter(content_type__app_label='communication')
        .values_list('content_type_id', 'codename')
    )
    print(f'  existing permissions for comm: {len(existing)}')
    
    # What we'd create
    to_create = []
    for model in app_config.get_models():
        ct = ct_map.get(model._meta.model_name)
        if ct is None:
            print(f'  WARNING: No CT for {model._meta.model_name}')
            continue
        for action in ('add', 'change', 'delete', 'view'):
            codename = f'{action}_{model._meta.model_name}'
            if (ct.pk, codename) not in existing:
                to_create.append(Permission(
                    name=f'Can {action} {model._meta.verbose_name}',
                    content_type_id=ct.pk,
                    codename=codename,
                ))
    
    if to_create:
        print(f'  Would create {len(to_create)} new permissions')
        for p in to_create[:3]:
            print(f'    content_type_id={p.content_type_id} codename={p.codename}')
    else:
        print(f'  No new permissions needed')

print('\nDone.')
