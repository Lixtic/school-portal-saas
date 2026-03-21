from django.conf import settings
from django.db import connection, close_old_connections
from django.http import Http404, HttpResponseRedirect
from django.urls import set_urlconf, set_script_prefix
from django_tenants.middleware.main import TenantMainMiddleware
from tenants.models import School
from urllib.parse import urlparse, parse_qsl, urlencode
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
            'dashboard', 'tenants', 'find-school', 'sw.js', 'offline',
            'about', 'contact', 'privacy', 'terms', 'health',
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
            # CRITICAL FIX for pgBouncer transaction mode + TENANT_LIMIT_SET_CALLS=True:
            # pgBouncer reassigns the physical PostgreSQL connection on each transaction.
            # If we reuse a Django connection (CONN_MAX_AGE>0) and the tenant is the
            # same as the previous request, set_tenant() sees search_path_set_schemas
            # already matching and skips SET search_path — but the physical connection
            # behind pgBouncer is fresh and has search_path="public".
            # Resetting here forces SET search_path on the first cursor of every request
            # while still only issuing it once per request (TENANT_LIMIT_SET_CALLS stays True).
            if hasattr(connection, 'search_path_set_schemas'):
                connection.search_path_set_schemas = None
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
                'dashboard', 'favicon.ico', 'favicon.png', 'favicon.svg',
                'robots.txt', 'sitemap.xml', 'debug', 'accounts', 'tenants', 'find-school',
                'password', 'reset', 'sw.js', 'offline', 'apple-touch-icon.png',
                'apple-touch-icon-precomposed.png',
                'about', 'contact', 'privacy', 'terms', 'health', ''
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

            if hasattr(connection, 'search_path_set_schemas'):
                connection.search_path_set_schemas = None
            connection.set_tenant(request.tenant)

    def process_view(self, request, view_func, view_args, view_kwargs):
        """Block access for schools whose trial has expired."""
        if not hasattr(request, 'tenant'):
            return None
        if request.tenant.schema_name == 'public':
            return None

        # CRITICAL (pgBouncer transaction mode + TENANT_LIMIT_SET_CALLS=True):
        # Use try/finally so that search_path_set_schemas is ALWAYS reset to None
        # before process_view returns, no matter which early-return path is taken.
        #
        # Why: In pgBouncer transaction mode every autocommit query (process_request,
        # auth middleware, here in process_view, …) may land on a different physical
        # PostgreSQL server connection whose search_path defaults to "public".
        # TENANT_LIMIT_SET_CALLS=True skips SET search_path when
        # search_path_set_schemas is already set — so a cached value from a previous
        # cursor would cause the *next* cursor to skip SET and hit the wrong schema.
        #
        # By resetting at the TOP (before any DB access, including the lazy
        # request.user lookup) and guaranteeing a reset at the BOTTOM via finally,
        # we ensure:
        #   (a) Every DB call inside process_view always re-issues SET search_path.
        #   (b) The ATOMIC_REQUESTS transaction that immediately follows also
        #       re-issues SET search_path on its first cursor.
        try:
            if hasattr(connection, 'search_path_set_schemas'):
                connection.search_path_set_schemas = None

            if not getattr(request, 'user', None) or not request.user.is_authenticated:
                return None

            path = request.path_info or '/'
            if any(path.startswith(p) for p in _TRIAL_EXEMPT_PATHS):
                return None

            try:
                from .models import SchoolSubscription
                from django.utils import timezone
                # Reset again before the subscription query — it may land on yet
                # another pgBouncer server connection.
                if hasattr(connection, 'search_path_set_schemas'):
                    connection.search_path_set_schemas = None
                sub = SchoolSubscription.objects.select_related('plan').get(school=request.tenant)
                # Cache on request so context processors and views don't re-query
                request._tenant_subscription = sub
                if sub.status == 'trial' and sub.trial_ends_at and timezone.now() > sub.trial_ends_at:
                    sub_url = f"/{request.tenant.schema_name}/tenants/subscription/"
                    logger.info("Trial expired for %s  redirecting to subscription page", request.tenant.schema_name)
                    return HttpResponseRedirect(sub_url)
            except SchoolSubscription.DoesNotExist:
                request._tenant_subscription = None  # Cache miss so context processors skip DB hit
            except Exception:
                pass  # Other DB errors — do not block access

            return None
        finally:
            # Always reset before returning so the ATOMIC_REQUESTS view transaction
            # re-issues SET search_path on its very first cursor.
            if hasattr(connection, 'search_path_set_schemas'):
                connection.search_path_set_schemas = None

    def process_response(self, request, response):
        """Normalize auth redirects so tenant pages don't bounce via public /login/."""
        try:
            if response.status_code not in (301, 302, 303, 307, 308):
                return response

            location = response.get('Location')
            if not location:
                return response

            parsed = urlparse(location)
            # Only rewrite local-path redirects that currently target public /login/
            if parsed.scheme or parsed.netloc or not parsed.path.startswith('/login/'):
                return response

            params = dict(parse_qsl(parsed.query, keep_blank_values=True))
            next_url = params.get('next', '')
            if not next_url.startswith('/'):
                return response

            next_parts = next_url.strip('/').split('/')
            tenant_hint = next_parts[0] if next_parts else ''
            if not tenant_hint:
                return response

            tenant_exists = School.objects.filter(schema_name=tenant_hint, is_active=True).exists()
            if not tenant_exists:
                return response

            new_params = dict(params)
            new_params['next'] = next_url
            query = urlencode(new_params)
            response['Location'] = f'/{tenant_hint}/login/?{query}'
        except Exception:
            # Never break responses due to redirect normalization issues.
            return response

        return response
