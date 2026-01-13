from django.conf import settings
from django.db import connection
from django.http import Http404
from django.urls import set_urlconf, set_script_prefix
from django_tenants.middleware.main import TenantMainMiddleware
from tenants.models import School

class TenantPathMiddleware(TenantMainMiddleware):
    def process_request(self, request):
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
            'signup', 'login', 'logout', 'debug', 'favicon.ico'
        ]
        
        if possible_schema and possible_schema != 'public' and possible_schema not in reserved_paths:
            # Try to find the school
            try:
                # Need to use the model class explicitly to avoid UnboundLocalError
                from tenants.models import School
                tenant = School.objects.filter(schema_name=possible_schema).first()
            except Exception:
                tenant = None
            
            # If we are here, it means the URL starts with something like /kings/
            # If no tenant is found, it's a 404. We shouldn't fall back to Public
            # because 'kings' isn't a valid page on the public site either.
            if not tenant:
                raise Http404(f"School '{possible_schema}' not found.")
        
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
                'dashboard', 'favicon.ico', 'debug', 'accounts',
                'password', 'reset'
            ]
            if possible_schema not in reserved_paths:
                print(f"DEBUG MIDDLEWARE: Tenant '{possible_schema}' not found and not reserved.")
                raise Http404(f"School '{possible_schema}' does not exist.")

            # === PUBLIC CONTEXT ===
            connection.set_tenant(public_tenant)
            request.tenant = public_tenant

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

