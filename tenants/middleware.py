from django.conf import settings
from django.db import connection, close_old_connections, transaction
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.urls import set_script_prefix
from django.contrib.auth import logout
from django_tenants.middleware.main import TenantMainMiddleware
from tenants.models import School, SchoolSubscription
from django.utils import timezone
from urllib.parse import urlparse, parse_qsl, urlencode
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def get_reserved_paths():
    """Reserved non-tenant paths — cached to avoid recomputation per request."""
    return {
        'static', 'media', 'admin', 'accounts', 'signup', 'login', 'logout',
        'debug', 'favicon.ico', 'favicon.png', 'apple-touch-icon.png',
        'apple-touch-icon-precomposed.png', 'favicon.svg', 'robots.txt',
        'sitemap.xml', 'dashboard', 'tenants', 'find-school', 'sw.js',
        'offline', 'about', 'contact', 'privacy', 'terms', 'health', 'landlord',
        'public', 'password', 'reset', 'i18n'
    }


@lru_cache(maxsize=1)
def get_tenant_app_roots():
    """Lazily load tenant app roots to avoid early-import circularities with settings."""
    _BASE_TENANT_APPS = getattr(settings, 'TENANT_APPS', [])
    return {app.split('.')[-1] for app in _BASE_TENANT_APPS} - {
        'admin', 'auth', 'contenttypes', 'sessions', 'messages', 'staticfiles',
        'humanize', 'crispy_forms', 'crispy_bootstrap5', 'django_tenants',
        'cloudinary', 'cloudinary_storage'
    }


@lru_cache(maxsize=1)
def get_reserved_paths_strict():
    return set(get_reserved_paths()) | get_tenant_app_roots() | {''}


def _is_ajax(request):
    """Return True if the request was sent via fetch/XHR expecting JSON."""
    return (
        request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        or request.headers.get('Accept', '').startswith('application/json')
    )


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
        # (e.g., /finance/), recover the tenant from session or same-origin referrer and redirect.
        tenant_app_roots = get_tenant_app_roots()
        reserved_paths = get_reserved_paths()
        reserved_paths_strict = get_reserved_paths_strict()
        
        if possible_schema in tenant_app_roots and len(path_parts) >= 1:
            recovery_schema = None

            # a. Try session-bound schema first (most reliable/secure source)
            session_schema = request.session.get('auth_tenant_schema') if hasattr(request, 'session') else None
            if session_schema and session_schema not in tenant_app_roots:
                try:
                    session_tenant = School.objects.filter(schema_name=session_schema, is_active=True).first()
                    if session_tenant:
                        recovery_schema = session_schema
                except Exception as e:
                    logger.debug("Tenant recovery lookup failed for session schema '%s': %s", session_schema, e, exc_info=True)

            # b. Fall back to HTTP_REFERER if session is unavailable
            if not recovery_schema:
                ref = request.META.get('HTTP_REFERER', '')
                try:
                    ref_path = urlparse(ref).path or ''
                    ref_first = ref_path.strip('/').split('/')[0] if ref_path else ''
                except Exception:
                    ref_first = ''

                if ref_first and ref_first not in tenant_app_roots and ref_first not in reserved_paths_strict:
                    try:
                        ref_tenant = School.objects.filter(schema_name=ref_first, is_active=True).first()
                        if ref_tenant:
                            recovery_schema = ref_first
                    except Exception as e:
                        logger.debug("Tenant recovery lookup failed for referrer schema '%s': %s", ref_first, e, exc_info=True)

            if recovery_schema:
                qs = request.META.get('QUERY_STRING', '')
                suffix = f"?{qs}" if qs else ''
                return HttpResponseRedirect(f"/{recovery_schema}{request.path}{suffix}")

        tenant = None

        # 3. Check if the first segment matches a valid School schema (excluding 'public')
        if possible_schema and possible_schema != 'public' and possible_schema not in reserved_paths:
            logger.debug("Checking tenant candidate: %s", possible_schema)
            try:
                tenant = School.objects.filter(schema_name=possible_schema).first()
            except Exception as e:
                logger.error("Tenant DB lookup error for %s: %s", possible_schema, e, exc_info=True)
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
            # pgBouncer transaction mode: reset before AND after set_tenant() so
            # every subsequent autocommit cursor (e.g. AuthenticationMiddleware's
            # User query) re-issues SET search_path on its actual physical connection.
            if hasattr(connection, 'search_path_set_schemas'):
                connection.search_path_set_schemas = None
            connection.set_tenant(request.tenant)
            if hasattr(connection, 'search_path_set_schemas'):
                connection.search_path_set_schemas = None

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
            if possible_schema and possible_schema not in reserved_paths_strict and possible_schema != 'public':
                logger.debug("Tenant '%s' not found and not reserved", possible_schema)
                raise Http404(f"School '{possible_schema}' does not exist.")

            # === PUBLIC CONTEXT ===
            try:
                public_schema = getattr(settings, 'PUBLIC_SCHEMA_NAME', 'public')
                request.tenant = School.objects.get(schema_name=public_schema)
            except Exception as e:
                logger.debug("Failed to pull public schema: %s", e, exc_info=True)
                request.tenant = School(schema_name='public', name='Public (Fallback)')

            if hasattr(connection, 'search_path_set_schemas'):
                connection.search_path_set_schemas = None
            connection.set_tenant(request.tenant)
            if hasattr(connection, 'search_path_set_schemas'):
                connection.search_path_set_schemas = None

    def process_view(self, request, view_func, view_args, view_kwargs):
        """Block access for schools whose trial has expired."""
        if not hasattr(request, 'tenant'):
            return None

        # ── Force-resolve request.user inside a transaction ──────────
        # AuthenticationMiddleware sets request.user as a SimpleLazyObject.
        # The actual DB query (User.objects.get) fires on first access.
        # On Neon (pgBouncer transaction mode), each autocommit statement
        # may land on a different physical PostgreSQL connection.
        # django-tenants issues SET search_path as a separate statement
        # from the SELECT, so in autocommit mode the SELECT can hit a
        # connection that still has search_path=public → user not found
        # → AnonymousUser → redirect to login on every request.
        #
        # Wrapping the first access in transaction.atomic() ensures
        # SET search_path + SELECT run in ONE transaction → pgBouncer
        # keeps them on the same physical server connection.
        if getattr(request, 'user', None) and request.tenant.schema_name != 'public':
            try:
                with transaction.atomic():
                    # Force the lazy object to resolve NOW, inside the txn.
                    _is_auth = request.user.is_authenticated  # noqa: F841
            except Exception as e:
                logger.debug("Failed to force-resolve user auth status: %s", e, exc_info=True)

        # Session isolation guard: auth sessions must stay bound to a single tenant schema.
        # Without this, a valid session from one tenant can be interpreted in another tenant
        # (ID collision risk across tenant-local auth tables).
        try:
            if getattr(request, 'user', None) and getattr(request.user, 'is_authenticated', False) and request.tenant.schema_name != 'public':
                current_schema = request.tenant.schema_name
                bound_schema = request.session.get('auth_tenant_schema')

                if bound_schema and bound_schema != current_schema:
                    logout(request)
                    if _is_ajax(request):
                        return JsonResponse(
                            {
                                'error': 'Your session belongs to a different school. Please sign in again.',
                                'redirect': f'/{current_schema}/login/',
                            },
                            status=401,
                        )
                    return HttpResponseRedirect(f'/{current_schema}/login/?next={request.path}')

                # Backfill for legacy sessions that predate tenant binding.
                if not bound_schema:
                    request.session['auth_tenant_schema'] = current_schema
        except Exception as e:
            logger.debug("Tenant session isolation validation failed: %s", e, exc_info=True)

        if request.tenant.schema_name == 'public':
            return None

        # Reset search_path cache before any DB access in this middleware phase.
        # With TENANT_LIMIT_SET_CALLS=False this is a harmless no-op, but it
        # provides defence-in-depth if the setting is ever re-enabled.
        try:
            if hasattr(connection, 'search_path_set_schemas'):
                connection.search_path_set_schemas = None

            if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
                return None

            path = request.path_info or '/'
            if any(path.startswith(p) for p in _TRIAL_EXEMPT_PATHS):
                return None

            try:
                sub = SchoolSubscription.objects.defer(
                    'paystack_subscription_code',
                    'paystack_customer_code',
                ).select_related('plan').get(school=request.tenant)
                
                request._tenant_subscription = sub
                if sub.status == 'trial' and sub.trial_ends_at and timezone.now() > sub.trial_ends_at:
                    sub_url = f"/{request.tenant.schema_name}/tenants/subscription/"
                    logger.info("Trial expired for %s  redirecting to subscription page", request.tenant.schema_name)
                    if _is_ajax(request):
                        return JsonResponse(
                            {'error': 'Your free trial has expired. Please subscribe to continue.',
                             'redirect': sub_url},
                            status=402,
                        )
                    return HttpResponseRedirect(sub_url)
            except SchoolSubscription.DoesNotExist:
                request._tenant_subscription = None
            except Exception as e:
                logger.debug("Failed validating school subscription: %s", e, exc_info=True)

            return None
        finally:
            if hasattr(connection, 'search_path_set_schemas'):
                connection.search_path_set_schemas = None

    def process_response(self, request, response):
        """Normalize auth redirects so tenant pages don't bounce via public /login/.

        Handles two cases:
        1. @login_required fires with SCRIPT_NAME unset → Location: /login/?next=/tenant/path/
           Rewrite to /{tenant}/login/?next=/tenant/path/
        2. @login_required fires with SCRIPT_NAME set → Location: /{tenant}/login/?next=/path/
           Already correct — but prepend tenant to 'next' so login_view can redirect back.
        """
        try:
            if response.status_code not in (301, 302, 303, 307, 308):
                return response

            location = response.get('Location')
            if not location:
                return response

            parsed = urlparse(location)
            # Only rewrite local-path redirects (no scheme/netloc = same-origin)
            if parsed.scheme or parsed.netloc:
                return response

            # Determine tenant context from the current request
            tenant_schema = getattr(getattr(request, 'tenant', None), 'schema_name', '')
            if not tenant_schema or tenant_schema == 'public':
                return response

            # Case 1: bare /login/ redirect (SCRIPT_NAME not set)
            if parsed.path == '/login/' or parsed.path == '/login':
                params = dict(parse_qsl(parsed.query, keep_blank_values=True))
                next_url = params.get('next', '')
                # If next already has tenant prefix, trust it; otherwise prepend
                if next_url and not next_url.startswith(f'/{tenant_schema}/'):
                    params['next'] = f'/{tenant_schema}{next_url}'
                query = urlencode(params)
                suffix = f'?{query}' if query else ''
                response['Location'] = f'/{tenant_schema}/login/{suffix}'
                return response

            # Case 2: tenant-prefixed login redirect — ensure next param has tenant prefix
            if parsed.path == f'/{tenant_schema}/login/' or parsed.path == f'/{tenant_schema}/login':
                params = dict(parse_qsl(parsed.query, keep_blank_values=True))
                next_url = params.get('next', '')
                if next_url and next_url.startswith('/') and not next_url.startswith(f'/{tenant_schema}/'):
                    params['next'] = f'/{tenant_schema}{next_url}'
                    query = urlencode(params)
                    response['Location'] = f'/{tenant_schema}/login/?{query}'
                return response

        except Exception as e:
            # Never break responses due to redirect normalization issues.
            logger.debug("Failed redirect normalization in process_response: %s", e, exc_info=True)
            return response

        return response
