"""
Custom PostgreSQL backend with automatic retry on stale connections for serverless environments.
Wraps django_tenants backend and catches InterfaceError (connection already closed).
"""
from django.db.utils import InterfaceError, OperationalError
from django_tenants.postgresql_backend.base import DatabaseWrapper as TenantDatabaseWrapper


class DatabaseWrapper(TenantDatabaseWrapper):
    """
    Custom wrapper that retries DB operations once if connection is stale.
    Solves "connection already closed" errors on Vercel/serverless platforms.
    """
    
    def _cursor(self, name=None):
        """
        Override _cursor to proactively ensure a live connection and retry once on stale sockets.
        This helps prevent "connection already closed" errors on serverless platforms.
        """
        try:
            # Proactively refresh if backend thinks connection is closed
            if getattr(self, 'connection', None) is None or getattr(self.connection, 'closed', False):
                self.close()
            self.ensure_connection()
            return super()._cursor(name)
        except InterfaceError as e:
            # Force reconnect then retry once
            if 'connection already closed' in str(e).lower() or 'closed' in str(e).lower():
                self.close()
                self.ensure_connection()
                return super()._cursor(name)
            raise
        except OperationalError as e:
            # Handle server-side disconnects
            if 'server closed the connection' in str(e).lower() or 'terminating connection' in str(e).lower():
                self.close()
                self.ensure_connection()
                return super()._cursor(name)
            raise
