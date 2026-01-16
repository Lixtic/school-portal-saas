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
        Override _cursor to catch InterfaceError and retry once with fresh connection.
        """
        try:
            return super()._cursor(name)
        except InterfaceError as e:
            # Connection was closed, force reconnect and retry once
            if 'connection already closed' in str(e).lower() or 'closed' in str(e).lower():
                # Close the stale connection
                self.close()
                # Retry - this will create a new connection
                return super()._cursor(name)
            # Re-raise if it's a different InterfaceError
            raise
        except OperationalError as e:
            # Also catch some operational errors that indicate stale connection
            if 'server closed the connection' in str(e).lower():
                self.close()
                return super()._cursor(name)
            raise
