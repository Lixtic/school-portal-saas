from django.conf import settings
from django.db import connection, close_old_connections
from django.http import Http404, HttpResponseRedirect
from django.urls import set_urlconf, set_script_prefix
from django_tenants.middleware.main import TenantMainMiddleware
from tenants.models import School
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

# Paths (relative to tenant root) that remain accessible after trial expiry
_TRIAL_EXEMPT_PATHS = (
    '/login/',
    '/logout/',
    '/tenants/subscription/',
    '/tenants/pricing/',
    '/password',  # password reset/change
    '/accounts/profile/',
)


class TenantPathMiddleware(TenantMainMiddleware):
    def process_request(self, request):
        # 0. Force close stale connections on serverless/Vercel before processing
        close_old_connections()

        # 1. Start with Public context to be safe
        connection.set_schema_to_public()

        # 2. Inspect Path
        path_parts = request.path.strip('/').split('/')
        possible_schema = path_parts[0] if path_parts else None

        # 2b. Recovery guard: if a tenant app path is hit without tenant prefix
        # (e.g., /finance/), recover the tenant from same-origin referrer and redirect.
        tenant_app_roots = {
            'teachers', 'students', 'parents', 'homework', 'academics',
            'announcements', 'communication', 'finance'
        }
        if possible_schema in tenant_app_roots and len(path_parts) >= 1:
            ref = request.META.get('HTTP_REFERER', '')
            try:
                ref_path = urlparse(ref).path or ''
                ref_first = ref_path.strip('/').split('/')[0] if ref_path else ''
            except Exception:
                ref_first = ''

            if ref_first and ref_first not in tenant_app_roots:
                if ref_first not in [
                    'static', 'media', 'admin', 'accounts', 'signup', 'login', 'logout', 'debug',
                    'favicon.ico', 'favicon.png', 'apple-touch-icon.png', 'apple-touch-icon-precomposed.png',
                    'favicon.svg', 'robots.txt', 'sitemap.xml', 'dashboard', 'tenants', 'find-school',
                    'sw.js', 'offline', 'public'
                ]:
                    ref_tenant = School.objects.filter(schema_name=ref_first, is_active=True).first()
                    if ref_tenant:
                        qs = request.META.get('QUERY_STRING', '')
                        suffix = f"?{qs}" if qs else ''
                        return HttpResponseRedirect(f"/{ref_first}{request.path}{suffix}")

        tenant = None

        # 3. Check if the first segment matches a valid School schema (excluding 'public')
        reserved_paths = [
            'static', 'media', 'admin', 'accounts',
            'signup', 'login', 'logout', 'debug', 'favicon.ico', 'favicon.png',
            'apple-touch-icon.png', 'apple-touch-icon-precomposed.png',
            'favicon.svg', 'robots.txt', 'sitemap.xml',
            'dashboard', 'tenants', 'find-school', 'sw.js', 'offline'
        ]

        if possible_schema and possible_schema != 'public' and possible_schema not in reserved_paths:
            logger.debug("Checking tenant candidate: %s", possible_schema)
            try:
                from tenants.models import School
                tenant = School.objects.filter(schema_name=possible_schema).first()
            except Exception as e:
                logger.error("Tenant DB lookup error for %s: %s", possible_schema, e)
                if settings.DEBUG:
                    raise e
                tenant = None

            if not tenant:
                logger.debug("Tenant '%s' looked up but returned None", possible_schema)
                if settings.DEBUG:
                    all_tenants = list(School.objects.values_list('schema_name', flat=True))
                    raise Http404(f"School '{possible_schema}' not found. Available schools in DB: {all_tenants}")
                raise Http404(f"School '{possible_schema}' not found in registry.")

            if not tenant.is_active:
                logger.info("Tenant '%s' is deactivated — blocking access.", possible_schema)
                raise Http404("This school is currently inactive.")

        if tenant:
            # === TENANT FOUND ===
            logger.debug("Tenant '%s' found. Rewriting URLs.", possible_schema)
            logger.debug("Original PATH_INFO=%s SCRIPT_NAME=%s", request.path_info, request.META.get('SCRIPT_NAME'))

            request.tenant = tenant
            connection.set_tenant(request.tenant)

            if request.path == f"/{possible_schema}":
                request.path_info = '/'

            if request.path.startswith(f"/{possible_schema}"):
                if not hasattr(request, '_original_script_prefix'):
                    request._original_script_prefix = request.META.get('SCRIPT_NAME', '')

                request.META['SCRIPT_NAME'] = f"/{possible_schema}"
                request.path_info = request.path[len(f"/{possible_schema}"):]

                if not request.path_info.startswith('/'):
                    request.path_info = '/' + request.path_info

                logger.debug("New PATH_INFO=%s SCRIPT_NAME=%s", request.path_info, request.META['SCRIPT_NAME'])
                set_script_prefix(f"/{possible_schema}")
            else:
                logger.warning("Path '%s' did not start with '/%s'", request.path, possible_schema)

        else:
            # === TENANT NOT FOUND ===
            reserved_paths_strict = [
                'admin', 'static', 'media', 'signup', 'login', 'logout',
                'dashboard', 'favicon.ico', 'debug', 'accounts', 'tenants', 'find-school',
                'password', 'reset', 'sw.js', 'offline', 'apple-touch-icon.png',
                'apple-touch-icon-precomposed.png', ''
            ]
            if possible_schema and possible_schema not in reserved_paths_strict and possible_schema != 'public':
                logger.debug("Tenant '%s' not found and not reserved", possible_schema)
                raise Http404(f"School '{possible_schema}' does not exist.")

            # === PUBLIC CONTEXT ===
            try:
                from tenants.models import School
                public_schema = getattr(settings, 'PUBLIC_SCHEMA_NAME', 'public')
                request.tenant = School.objects.get(schema_name=public_schema)
            except Exception:
                from tenants.models import School
                request.tenant = School(schema_name='public', name='Public (Fallback)')

            connection.set_tenant(request.tenant)

    def process_view(self, request, view_func, view_args, view_kwargs):
        """Block access for schools whose trial has expired."""
        if not hasattr(request, 'tenant'):
            return None
        if request.tenant.schema_name == 'public':
            return None
        if not getattr(request, 'user', None) or not request.user.is_authenticated:
            return None

        path = request.path_info or '/'
        if any(path.startswith(p) for p in _TRIAL_EXEMPT_PATHS):
            return None

        try:
            from .models import SchoolSubscription
            from django.utils import timezone
            sub = SchoolSubscription.objects.select_related('plan').get(school=request.tenant)
            if sub.status == 'trial' and sub.trial_ends_at and timezone.now() > sub.trial_ends_at:
                sub_url = f"/{request.tenant.schema_name}/tenants/subscription/"
                logger.info("Trial expired for %s  redirecting to subscription page", request.tenant.schema_name)
                return HttpResponseRedirect(sub_url)
        except Exception:
            pass  # Missing subscription or DB error  do not block access

        return None
