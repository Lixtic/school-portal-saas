from django.conf import settings
from django.db import connection, close_old_connections
from django.http import Http404
from django.urls import set_urlconf, set_script_prefix
from django_tenants.middleware.main import TenantMainMiddleware
from tenants.models import School

class TenantPathMiddleware(TenantMainMiddleware):
    def process_request(self, request):
        # 0. Force close stale connections on serverless/Vercel before processing
        close_old_connections()
        
        # 1. Start with Public context to be safe
        connection.set_schema_to_public()
        
        # 2. Inspect Path
        path_parts = request.path.strip('/').split('/')
        possible_schema = path_parts[0] if path_parts else None
        
        tenant = None

        # 3. Check if the first segment matches a valid School schema (excluding 'public')
        # Add common global paths to exclude from tenant lookup
        reserved_paths = [
            'static', 'media', 'admin', 'accounts', 
            'signup', 'login', 'logout', 'debug', 'favicon.ico', 'dashboard', 'tenants'
        ]
        
        if possible_schema and possible_schema != 'public' and possible_schema not in reserved_paths:
            print(f"DEBUG MIDDLEWARE: Checking tenant candidate: {possible_schema}")
            # Try to find the school
            try:
                # Need to use the model class explicitly to avoid UnboundLocalError
                from tenants.models import School
                tenant = School.objects.filter(schema_name=possible_schema).first()
            except Exception as e:
                print(f"DEBUG MIDDLEWARE: DB Lookup Error: {e}")
                if settings.DEBUG:
                     # Re-raise to see the actual database error (e.g. missing column)
                     raise e
                tenant = None
            
            # If we are here, it means the URL starts with something like /kings/
            # If no tenant is found, it's a 404. We shouldn't fall back to Public
            # because 'kings' isn't a valid page on the public site either.
            if not tenant:
                print(f"DEBUG MIDDLEWARE: Tenant '{possible_schema}' looked up but returned None.")
                if settings.DEBUG:
                     # List available tenants to help user debug
                     all_tenants = list(School.objects.values_list('schema_name', flat=True))
                     raise Http404(f"School '{possible_schema}' not found. Available schools in DB: {all_tenants}")
                raise Http404(f"School '{possible_schema}' not found in registry.")
        
        if tenant:

            # === TENANT FOUND ===
            print(f"DEBUG MIDDLEWARE: Tenant '{possible_schema}' found. Rewriting URLs.")
            print(f"DEBUG MIDDLEWARE: Original PATH_INFO: {request.path_info}")
            print(f"DEBUG MIDDLEWARE: Original SCRIPT_NAME: {request.META.get('SCRIPT_NAME')}")
            
            request.tenant = tenant
            connection.set_tenant(request.tenant)
            
            # Setup URL Routing for Tenant Apps
            
            script_prefix = f"/{possible_schema}/"
            # Normalize path to ensure we can split correct (e.g. /kings -> /kings/)
            if request.path == f"/{possible_schema}":
                 request.path_info = '/'
            
            if request.path.startswith(f"/{possible_schema}"):
                # Save original
                if not hasattr(request, '_original_script_prefix'):
                     request._original_script_prefix = request.META.get('SCRIPT_NAME', '')

                # Rewrite
                request.META['SCRIPT_NAME'] = f"/{possible_schema}"
                request.path_info = request.path[len(f"/{possible_schema}"):]
                
                # Ensure leading slash
                if not request.path_info.startswith('/'):
                    request.path_info = '/' + request.path_info
                
                print(f"DEBUG MIDDLEWARE: New PATH_INFO: {request.path_info}")
                print(f"DEBUG MIDDLEWARE: New SCRIPT_NAME: {request.META['SCRIPT_NAME']}")

                # Activate
                set_script_prefix(f"/{possible_schema}")
            else:
                 print(f"DEBUG MIDDLEWARE: Path '{request.path}' did not start with '/{possible_schema}'? Strange.")

        else:
            # === TENANT NOT FOUND ===
            # If it looks like a tenant path (not a reserved public path), raise 404 immediately
            # identifying that the school itself doesn't exist.
            reserved_paths = [
                'admin', 'static', 'media', 'signup', 'login', 'logout', 
                'dashboard', 'favicon.ico', 'debug', 'accounts', 'tenants',
                'password', 'reset', ''
            ]
            # Ensure we don't treat root path (empty string) as a missing tenant
            if possible_schema and possible_schema not in reserved_paths and possible_schema != 'public':
                print(f"DEBUG MIDDLEWARE: Tenant '{possible_schema}' not found and not reserved.")
                raise Http404(f"School '{possible_schema}' does not exist.")

            # === PUBLIC CONTEXT ===
            # No tenant found in path -> Serve Public Site
            try:
                # Need to use the model class explicitly here too
                from tenants.models import School
                public_schema = getattr(settings, 'PUBLIC_SCHEMA_NAME', 'public')
                request.tenant = School.objects.get(schema_name=public_schema)
            except Exception: # Catch both DoesNotExist and UnboundLocal if weird things happen

                # Fallback if DB is empty / public tenant missing
                # This should be handled by WSGI hook now, but just in case
                from tenants.models import School
                request.tenant = School(schema_name='public', name='Public (Fallback)')
                
            connection.set_tenant(request.tenant)
            # self.setup_url_routing(request)

