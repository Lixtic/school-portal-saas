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
        if possible_schema and possible_schema != 'public' and possible_schema not in ['static', 'media', 'admin', 'accounts']:
            # Try to find the school
            tenant = School.objects.filter(schema_name=possible_schema).first()
        
        if tenant:
            # === TENANT FOUND ===
            request.tenant = tenant
            connection.set_tenant(request.tenant)
            
            # Setup URL Routing for Tenant Apps
            # This points to the standard urls.py which routes to academics, students, etc.
            # IMPT: We are NOT stripping the prefix here because it messes up 'reverse()' 
            # and form actions unless we use complex SCRIPT_NAME hacks.
            # Instead, we will prefix the tenant URLs in the main urls.py?
            # 
            # Wait, if we don't strip it, the tenant's urls.py needs to expect 'school1/dashboard/'
            # That is impossible to maintain dynamically.
            #
            # The standard Django way for sub-path apps is modifying SCRIPT_NAME.
            # request.META['SCRIPT_NAME'] = '/' + possible_schema
            # request.META['PATH_INFO'] = request.path[len(possible_schema)+1:] 
            
            # Let's try the SCRIPT_NAME approach.
            # Original: /school1/dashboard/
            # SCRIPT_NAME: /school1
            # PATH_INFO: /dashboard/
            
            script_prefix = f"/{possible_schema}/"
            if request.path.startswith(script_prefix[:-1]) and '/' in request.path[1:]: 
               # We need to handle cases like /school1 (no trailing slash) -> /school1/
               pass

            if request.path.startswith(f"/{possible_schema}"):
                # Save original path info for potential restoration (if needed, though requests are one-way)
                if not hasattr(request, '_original_script_prefix'):
                     request._original_script_prefix = request.META.get('SCRIPT_NAME', '')

                # Force ensure path ends with slash if it's just the root
                # if request.path == f"/{possible_schema}":
                #    return redirect(f"/{possible_schema}/")

                # Update SCRIPT_NAME to include the tenant prefix
                # E.g. /school1/login/ -> SCRIPT_NAME=/school1, PATH_INFO=/login/
                request.META['SCRIPT_NAME'] = f"/{possible_schema}"
                request.path_info = request.path[len(f"/{possible_schema}"):]
                
                # Fix for empty path_info which Django hates (must start with /)
                if not request.path_info or not request.path_info.startswith('/'):
                    request.path_info = '/' + request.path_info
                
                # IMPORTANT: Activate the new urlconf behavior
                set_script_prefix(f"/{possible_schema}")

            # self.setup_url_routing(request) 
            # DONT call setup_url_routing! 
            # In django-tenants, setup_url_routing usually forces the ROOT_URLCONF to a tenant specific one.
            # But we are using the SAME urls.py file for everyone (path routing strategy).
            # If we let it switch urls, it might look for 'school.urls' which doesn't exist.
            # We want to stick to 'school_system.urls' but just strip the prefix.
            
        else:
            # === PUBLIC CONTEXT ===
            # No tenant found in path -> Serve Public Site
            try:
                public_schema = getattr(settings, 'PUBLIC_SCHEMA_NAME', 'public')
                request.tenant = School.objects.get(schema_name=public_schema)
            except School.DoesNotExist:
                # Fallback if DB is empty / public tenant missing
                # This should be handled by WSGI hook now, but just in case
                from tenants.models import School
                request.tenant = School(schema_name='public', name='Public (Fallback)')
                
            connection.set_tenant(request.tenant)
            # self.setup_url_routing(request)

