"""
Custom PostgreSQL backend with automatic retry on stale connections for serverless environments.
Wraps django_tenants backend and catches InterfaceError (connection already closed).
"""
from django.db.utils import InterfaceError, OperationalError
from django_tenants.postgresql_backend.base import DatabaseWrapper as TenantDatabaseWrapper
import logging

logger = logging.getLogger(__name__)


class DatabaseWrapper(TenantDatabaseWrapper):
    """
    Custom wrapper that retries DB operations once if connection is stale.
    Solves "connection already closed" errors on Vercel/serverless platforms.
    """
    
    def _force_reconnect(self):
        """Aggressively close and reset connection"""
        try:
            if self.connection is not None:
                try:
                    self.connection.close()
                except Exception:
                    pass
            self.close()
            # Reset connection to None to force recreation
            self.connection = None
        except Exception as e:
            logger.warning(f"Error during force reconnect: {e}")
    
    def _cursor(self, name=None):
        """
        Override _cursor to proactively ensure a live connection and retry once on stale sockets.
        This helps prevent "connection already closed" errors on serverless platforms.
        """
        retry_count = 0
        max_retries = 2
        
        while retry_count <= max_retries:
            try:
                # Check if connection appears closed
                if retry_count > 0 or (self.connection is not None and hasattr(self.connection, 'closed') and self.connection.closed):
                    self._force_reconnect()
                
                self.ensure_connection()
                return super()._cursor(name)
                
            except (InterfaceError, OperationalError) as e:
                error_msg = str(e).lower()
                is_connection_error = (
                    'connection already closed' in error_msg or
                    'closed' in error_msg or
                    'server closed the connection' in error_msg or
                    'terminating connection' in error_msg
                )
                
                if is_connection_error and retry_count < max_retries:
                    retry_count += 1
                    logger.warning(f"Stale connection detected (attempt {retry_count}/{max_retries}): {e}")
                    self._force_reconnect()
                    continue
                raise
