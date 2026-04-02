from django.conf import settings
from django.db import connection, close_old_connections, transaction
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.urls import set_script_prefix
from django.contrib.auth import logout
from django.contrib.auth.models import AnonymousUser
from django_tenants.middleware.main import TenantMainMiddleware
from tenants.models import School, SchoolSubscription
from django.utils import timezone
from urllib.parse import urlparse, parse_qsl, urlencode
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


# ── Cached Path Sets ──────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_reserved_paths():
    """Reserved non-tenant URL segments — cached once per process."""
    return frozenset({
        'static', 'media', 'admin', 'accounts', 'signup', 'login', 'logout', 'u',
        'debug', 'favicon.ico', 'favicon.png', 'apple-touch-icon.png',
        'apple-touch-icon-precomposed.png', 'favicon.svg', 'robots.txt',
        'sitemap.xml', 'dashboard', 'tenants', 'find-school', 'sw.js',
        'offline', 'about', 'contact', 'privacy', 'terms', 'health', 'landlord',
        'public', 'password', 'reset', 'i18n',
    })


@lru_cache(maxsize=1)
def get_tenant_app_roots():
    """App-label segments that could collide with tenant slugs."""
    _apps = getattr(settings, 'TENANT_APPS', [])
    _framework = {
        'admin', 'auth', 'contenttypes', 'sessions', 'messages', 'staticfiles',
        'humanize', 'crispy_forms', 'crispy_bootstrap5', 'django_tenants',
        'cloudinary', 'cloudinary_storage',
    }
    return frozenset({app.split('.')[-1] for app in _apps} - _framework)


@lru_cache(maxsize=1)
def get_all_reserved():
    """Union of reserved paths + tenant app roots + empty string."""
    return get_reserved_paths() | get_tenant_app_roots() | frozenset({'', 'public'})


# ── Helpers ───────────────────────────────────────────────────────────────────

def _is_ajax(request):
    """Return True if the request expects a JSON response."""
    return (
        request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        or request.headers.get('Accept', '').startswith('application/json')
    )


def _reset_search_path():
    """Clear cached search_path so next query re-issues SET search_path."""
    if hasattr(connection, 'search_path_set_schemas'):
        connection.search_path_set_schemas = None


def _set_tenant_on_connection(tenant):
    """Set tenant schema on connection, resetting search_path cache around it."""
    _reset_search_path()
    connection.set_tenant(tenant)
    _reset_search_path()


def _get_public_tenant():
    """Return the public schema tenant, with a safe fallback."""
    public_name = getattr(settings, 'PUBLIC_SCHEMA_NAME', 'public')
    try:
        return School.objects.get(schema_name=public_name)
    except Exception:
        return School(schema_name='public', name='Public (Fallback)')


# Paths (relative to tenant root) that stay accessible after trial expiry.
_TRIAL_EXEMPT_PATHS = (
    '/login/',
    '/logout/',
    '/tenants/subscription/',
    '/tenants/pricing/',
    '/password',
    '/accounts/profile/',
)


# ── Middleware ─────────────────────────────────────────────────────────────────

class TenantPathMiddleware(TenantMainMiddleware):
    """
    Path-based multi-tenancy middleware.

    URL structure:  /<schema_name>/app/view/
    - Parses the first path segment to identify the tenant.
    - Rewrites SCRIPT_NAME / path_info so url reversals produce correct URLs.
    - Falls back to the public schema for non-tenant paths.

    Also handles (in process_view, after auth middleware runs):
    - pgBouncer user resolution
    - Cross-tenant session isolation
    - Subscription / trial expiry gating
    """

    # ── Request Phase ─────────────────────────────────────────────────────

    def process_request(self, request):
        close_old_connections()
        connection.set_schema_to_public()

        slug = self._extract_slug(request)
        all_reserved = get_all_reserved()

        # Recover bare app-root hits (e.g. /finance/) to the correct tenant.
        if slug in get_tenant_app_roots():
            return self._recover_tenant_redirect(request, slug, all_reserved)

        tenant = self._resolve_tenant(slug, all_reserved)

        if tenant:
            self._activate_tenant(request, tenant, slug)
        else:
            self._activate_public(request)

    # ── View Phase ────────────────────────────────────────────────────────

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not hasattr(request, 'tenant'):
            return None

        is_tenant_ctx = request.tenant.schema_name != 'public'

        if is_tenant_ctx:
            self._force_resolve_user(request)
            self._verify_user_in_tenant(request)
            response = self._enforce_session_isolation(request)
            if response:
                return response

        if not is_tenant_ctx:
            return None

        _reset_search_path()
        try:
            return self._check_trial_expiry(request)
        finally:
            _reset_search_path()

    # ── Response Phase ────────────────────────────────────────────────────

    def process_response(self, request, response):
        if response.status_code not in (301, 302, 303, 307, 308):
            return response

        location = response.get('Location', '')
        if not location:
            return response

        parsed = urlparse(location)
        if parsed.scheme or parsed.netloc:
            return response  # external redirect — leave untouched

        tenant_schema = getattr(getattr(request, 'tenant', None), 'schema_name', '')
        if not tenant_schema or tenant_schema == 'public':
            return response

        try:
            response['Location'] = self._normalize_login_redirect(
                parsed, tenant_schema
            ) or location
        except Exception as exc:
            logger.debug("Redirect normalization error: %s", exc, exc_info=True)

        return response

    # ══════════════════════════════════════════════════════════════════════
    #  Private helpers
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    def _extract_slug(request):
        """Return the first path segment (candidate tenant slug)."""
        parts = request.path.strip('/').split('/')
        return parts[0] if parts else ''

    # ── Tenant Resolution ─────────────────────────────────────────────────

    def _resolve_tenant(self, slug, all_reserved):
        """Look up a School by schema_name.  Returns None for public context."""
        if not slug or slug in all_reserved:
            return None

        logger.debug("Tenant lookup: %s", slug)
        try:
            tenant = School.objects.filter(schema_name=slug).first()
        except Exception as exc:
            logger.error("Tenant DB error for '%s': %s", slug, exc, exc_info=True)
            if settings.DEBUG:
                raise
            raise Http404(f"School '{slug}' lookup failed.") from exc

        if tenant is None:
            if settings.DEBUG:
                all_names = list(School.objects.values_list('schema_name', flat=True))
                raise Http404(
                    f"School '{slug}' not found. Available: {all_names}"
                )
            raise Http404(f"School '{slug}' not found in registry.")

        if not tenant.is_active:
            logger.info("Tenant '%s' is deactivated.", slug)
            raise Http404("This school is currently inactive.")

        return tenant

    # ── Activation ────────────────────────────────────────────────────────

    def _activate_tenant(self, request, tenant, slug):
        """Switch to tenant schema and rewrite SCRIPT_NAME / path_info."""
        request.tenant = tenant
        _set_tenant_on_connection(tenant)

        prefix = f"/{slug}"
        if request.path == prefix:
            request.path_info = '/'
        elif request.path.startswith(prefix):
            if not hasattr(request, '_original_script_prefix'):
                request._original_script_prefix = request.META.get('SCRIPT_NAME', '')
            request.META['SCRIPT_NAME'] = prefix
            tail = request.path[len(prefix):]
            request.path_info = tail if tail.startswith('/') else f"/{tail}"
        else:
            logger.warning("Path '%s' doesn't start with '/%s'", request.path, slug)

        set_script_prefix(prefix)
        logger.debug("Tenant active: schema=%s  path_info=%s", slug, request.path_info)

    def _activate_public(self, request):
        """Fall back to the public schema."""
        request.tenant = _get_public_tenant()
        _set_tenant_on_connection(request.tenant)

    # ── Bare-App Recovery ─────────────────────────────────────────────────

    def _recover_tenant_redirect(self, request, slug, all_reserved):
        """
        When a user hits /finance/ (an app root without tenant prefix),
        try to recover the correct tenant from the session or referrer
        and redirect to /<tenant>/finance/...
        """
        schema = self._recover_schema_from_session(request, all_reserved)
        if not schema:
            schema = self._recover_schema_from_referrer(request, all_reserved)

        if schema:
            qs = request.META.get('QUERY_STRING', '')
            suffix = f"?{qs}" if qs else ''
            return HttpResponseRedirect(f"/{schema}{request.path}{suffix}")

        return HttpResponseRedirect('/find-school/')

    def _recover_schema_from_session(self, request, all_reserved):
        if not hasattr(request, 'session'):
            return None
        schema = request.session.get('auth_tenant_schema')
        if not schema or schema in all_reserved:
            return None
        try:
            if School.objects.filter(schema_name=schema, is_active=True).exists():
                return schema
        except Exception as exc:
            logger.debug("Session recovery failed for '%s': %s", schema, exc)
        return None

    def _recover_schema_from_referrer(self, request, all_reserved):
        ref = request.META.get('HTTP_REFERER', '')
        if not ref:
            return None
        try:
            first = urlparse(ref).path.strip('/').split('/')[0]
        except Exception:
            return None
        if not first or first in all_reserved:
            return None
        try:
            if School.objects.filter(schema_name=first, is_active=True).exists():
                return first
        except Exception as exc:
            logger.debug("Referrer recovery failed for '%s': %s", first, exc)
        return None

    # ── User Resolution (pgBouncer-safe) ──────────────────────────────────

    @staticmethod
    def _force_resolve_user(request):
        """
        Resolve the lazy user object inside a transaction so that
        SET search_path + SELECT share the same pgBouncer connection.
        """
        if not hasattr(request, 'user'):
            return
        try:
            with transaction.atomic():
                _ = request.user.is_authenticated  # force resolution
        except Exception as exc:
            logger.debug("User resolution failed: %s", exc, exc_info=True)
            request.user = AnonymousUser()

    @staticmethod
    def _verify_user_in_tenant(request):
        """
        Ensure the authenticated user actually exists in this tenant's
        accounts_user table (not just via the public schema fallback).
        """
        if not getattr(request.user, 'is_authenticated', False):
            return
        schema = request.tenant.schema_name.replace('"', '')
        try:
            with connection.cursor() as cur:
                cur.execute(
                    f'SELECT 1 FROM "{schema}".accounts_user WHERE id = %s LIMIT 1',
                    [request.user.pk],
                )
                if cur.fetchone() is None:
                    logger.info(
                        "User pk=%s not in tenant '%s' — demoting to AnonymousUser",
                        request.user.pk, schema,
                    )
                    request.user = AnonymousUser()
        except Exception as exc:
            logger.debug("Tenant user check error: %s", exc, exc_info=True)

    # ── Session Isolation ─────────────────────────────────────────────────

    def _enforce_session_isolation(self, request):
        """
        If the user's session was created under a different tenant,
        log them out and redirect to this tenant's login page.
        """
        user = getattr(request, 'user', None)
        if not user or not getattr(user, 'is_authenticated', False):
            return None

        current = request.tenant.schema_name
        bound = request.session.get('auth_tenant_schema')

        if bound and bound != current:
            logout(request)
            login_url = f'/{current}/login/?next={request.path}'
            if _is_ajax(request):
                return JsonResponse(
                    {'error': 'Session belongs to a different school. Please sign in again.',
                     'redirect': f'/{current}/login/'},
                    status=401,
                )
            return HttpResponseRedirect(login_url)

        # Back-fill for sessions created before tenant binding was added.
        if not bound:
            request.session['auth_tenant_schema'] = current

        return None

    # ── Subscription / Trial Gating ───────────────────────────────────────

    @staticmethod
    def _check_trial_expiry(request):
        """Block access if the school's free trial has expired."""
        user = getattr(request, 'user', None)
        if not user or not getattr(user, 'is_authenticated', False):
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
                logger.info("Trial expired for '%s'", request.tenant.schema_name)
                if _is_ajax(request):
                    return JsonResponse(
                        {'error': 'Your free trial has expired. Please subscribe to continue.',
                         'redirect': sub_url},
                        status=402,
                    )
                return HttpResponseRedirect(sub_url)
        except SchoolSubscription.DoesNotExist:
            request._tenant_subscription = None
        except Exception as exc:
            logger.debug("Subscription check error: %s", exc, exc_info=True)

        return None

    # ── Login Redirect Normalization ──────────────────────────────────────

    @staticmethod
    def _normalize_login_redirect(parsed, tenant_schema):
        """
        Rewrite login redirects so @login_required bounces to the correct
        tenant login URL with a proper `next` parameter.

        Returns the corrected Location string, or None to keep the original.
        """
        prefix = f'/{tenant_schema}'
        login_bare = '/login/'
        login_tenant = f'{prefix}/login/'

        # Case 1: bare /login/ → /<tenant>/login/?next=/<tenant>/…
        if parsed.path in ('/login/', '/login'):
            params = dict(parse_qsl(parsed.query, keep_blank_values=True))
            next_url = params.get('next', '')
            if next_url and not next_url.startswith(prefix + '/'):
                params['next'] = f'{prefix}{next_url}'
            qs = urlencode(params)
            return f'{login_tenant}?{qs}' if qs else login_tenant

        # Case 2: /<tenant>/login/ — ensure next has tenant prefix
        if parsed.path in (login_tenant, login_tenant.rstrip('/')):
            params = dict(parse_qsl(parsed.query, keep_blank_values=True))
            next_url = params.get('next', '')
            if next_url and next_url.startswith('/') and not next_url.startswith(prefix + '/'):
                params['next'] = f'{prefix}{next_url}'
                qs = urlencode(params)
                return f'{login_tenant}?{qs}'

        return None
