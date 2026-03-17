"""
Tenant-aware database session backend.

Wraps Django's default ``django.contrib.sessions.backends.db`` and
explicitly sets the PostgreSQL ``search_path`` to the current tenant
schema before **every** session DB operation (load / save / delete /
exists / clear_expired).

Why this is necessary
---------------------
``django.contrib.sessions`` is in both ``SHARED_APPS`` and
``TENANT_APPS``, so every tenant schema owns its own
``django_session`` table.  ``django-tenants`` normally keeps the
``search_path`` in sync via its ``_cursor()`` hook, but there are
edge cases on serverless hosts (Vercel cold starts, Neon PgBouncer
connection pooling, ``close_old_connections()`` timing) where the
search_path can briefly point at the wrong schema.

If the session is read from the wrong schema, it comes back empty.
Django's ``get_user()`` then fails the ``_auth_user_hash`` check and
calls ``session.flush()`` — **permanently destroying** the real
session.  The user is logged out on the next request.

By forcing ``SET search_path`` immediately before every session query
we guarantee the correct table is hit regardless of connection state.
"""

import logging
from django.contrib.sessions.backends.db import SessionStore as _DBStore
from django.db import connection

logger = logging.getLogger('session.tenant')


def _ensure_tenant_schema():
    """Force the DB search_path to match the current tenant schema.

    Resets ``search_path_set_schemas`` so that django-tenants' next
    ``_cursor()`` call will issue an explicit ``SET search_path``.
    """
    schema = getattr(connection, 'schema_name', None)
    if not schema:
        return
    # Invalidate the cached search_path so the next cursor call re-issues SET.
    connection.search_path_set_schemas = None


class SessionStore(_DBStore):
    """Drop-in replacement for ``django.contrib.sessions.backends.db``
    that guarantees the tenant schema is active for every DB hit."""

    def load(self):
        _ensure_tenant_schema()
        return super().load()

    def exists(self, session_key):
        _ensure_tenant_schema()
        return super().exists(session_key)

    def save(self, must_create=False):
        _ensure_tenant_schema()
        return super().save(must_create=must_create)

    def delete(self, session_key=None):
        _ensure_tenant_schema()
        return super().delete(session_key)

    @classmethod
    def clear_expired(cls):
        _ensure_tenant_schema()
        return super().clear_expired()
