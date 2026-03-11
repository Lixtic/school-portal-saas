from django.apps import AppConfig


class TenantsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tenants'

    def ready(self):
        # Patch Django's post_migrate signal handlers so migrate_schemas doesn't
        # crash with UniqueViolation / FK errors when content types or
        # permissions already exist in pre-populated tenant schemas.
        #
        # Strategy: disconnect the originals and swap in thin wrappers that
        # call bulk_create(..., ignore_conflicts=True) instead of the default
        # behaviour, which does NOT use ignore_conflicts and aborts the whole
        # PostgreSQL transaction on a duplicate-key error.
        from django.db import DEFAULT_DB_ALIAS, router
        from django.db.models.signals import post_migrate
        from django.contrib.contenttypes.management import (
            create_contenttypes,
            get_contenttypes_and_models,
        )
        from django.contrib.auth.management import create_permissions

        def _safe_create_contenttypes(
            app_config, verbosity=2, interactive=True,
            using=DEFAULT_DB_ALIAS, apps=None, **kwargs
        ):
            from django.apps import apps as global_apps
            from django.contrib.contenttypes.models import ContentType as CT

            _apps = apps or global_apps
            if not app_config.models_module:
                return
            try:
                cfg = _apps.get_app_config(app_config.label)
                CTModel = _apps.get_model('contenttypes', 'ContentType')
            except LookupError:
                return
            if not router.allow_migrate_model(using, CTModel):
                return

            # Clear cache so we read from the current schema
            CT.objects.clear_cache()

            content_types, app_models = get_contenttypes_and_models(cfg, using, CTModel)
            if not app_models:
                return

            cts = [
                CTModel(app_label=app_config.label, model=model_name)
                for model_name in app_models
                if model_name not in (content_types or {})
            ]
            if cts:
                CTModel.objects.using(using).bulk_create(cts, ignore_conflicts=True)

        def _safe_create_permissions(
            app_config, verbosity=2, interactive=True,
            using=DEFAULT_DB_ALIAS, apps=None, **kwargs
        ):
            from django.apps import apps as global_apps
            from django.contrib.auth.models import Permission
            from django.contrib.contenttypes.models import ContentType

            _apps = apps or global_apps
            if not router.allow_migrate_model(using, Permission):
                return
            try:
                app_config_obj = _apps.get_app_config(app_config.label)
            except LookupError:
                return

            # Clear the ContentType cache so we get IDs from the CURRENT schema,
            # not from a previously-processed schema.
            ContentType.objects.clear_cache()

            # Build content-type map for this app using raw DB values only
            ct_map = {}
            for ct in ContentType.objects.using(using).filter(
                app_label=app_config.label
            ):
                # Attach the object to the correct content type so FK is valid
                ct_map[ct.model] = ct

            if not ct_map:
                return

            # Existing (content_type_id, codename) pairs — use raw DB IDs
            existing = set(
                Permission.objects.using(using)
                .filter(content_type__app_label=app_config.label)
                .values_list('content_type_id', 'codename')
            )

            to_create = []
            for model in app_config_obj.get_models():
                ct = ct_map.get(model._meta.model_name)
                if ct is None:
                    continue
                # Use ct.pk — freshly fetched from the current schema
                for action in ('add', 'change', 'delete', 'view'):
                    codename = f'{action}_{model._meta.model_name}'
                    if (ct.pk, codename) not in existing:
                        to_create.append(Permission(
                            name=f'Can {action} {model._meta.verbose_name}',
                            content_type_id=ct.pk,  # Use raw PK, not ORM object
                            codename=codename,
                        ))

            if to_create:
                import sys
                from django.db import transaction
                print(
                    f'[TENANTS] Creating {len(to_create)} permissions '
                    f'for {app_config.label} '
                    f'(ct_ids={sorted({p.content_type_id for p in to_create})})',
                    file=sys.stderr,
                )
                try:
                    with transaction.atomic(using=using, savepoint=True):
                        Permission.objects.using(using).bulk_create(
                            to_create, ignore_conflicts=True
                        )
                except Exception:
                    # FK violation can occur when tenant-schema content type IDs
                    # are used in the public-schema permission write (schema
                    # switching race in post_migrate). Safe to skip.
                    pass

        def _patch_signal_handlers():
            """Disconnect Django's built-in handlers and swap in safe wrappers.

            Called once immediately (in case 'tenants' comes after auth in
            INSTALLED_APPS) AND deferred via the first post_migrate so that
            if auth.ready() connects create_permissions AFTER us, we catch it
            before any migrations fire.
            """
            # Replace create_contenttypes (connected without dispatch_uid)
            post_migrate.disconnect(create_contenttypes)
            post_migrate.connect(_safe_create_contenttypes)

            # Replace create_permissions (connected with dispatch_uid)
            post_migrate.disconnect(
                dispatch_uid='django.contrib.auth.management.create_permissions'
            )
            post_migrate.connect(
                _safe_create_permissions,
                dispatch_uid='django.contrib.auth.management.create_permissions',
            )

        # Apply immediately — works when 'tenants' is after auth in INSTALLED_APPS.
        _patch_signal_handlers()

        # Belt-and-suspenders: re-apply on the very first post_migrate signal
        # so that even if auth connects create_permissions after us (e.g. due to
        # app ordering changes), we overwrite it before the second schema runs.
        _patch_applied = [False]

        def _ensure_patch(sender, **kwargs):
            if not _patch_applied[0]:
                _patch_applied[0] = True
                _patch_signal_handlers()

        post_migrate.connect(_ensure_patch)
