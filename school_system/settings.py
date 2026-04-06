"""
Django settings for school_system project.
"""

import os
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

DEFAULT_SECRET_KEY = 'django-insecure-your-secret-key-here-change-in-production'

# SECURITY WARNING: keep the secret key used in production secret!
# Accepts SECRET_KEY, DJANGO_SECRET_KEY, or SECRET_KEY_BASE env vars.
SECRET_KEY = (
    os.environ.get('SECRET_KEY')
    or os.environ.get('DJANGO_SECRET_KEY')
    or os.environ.get('SECRET_KEY_BASE')
    or DEFAULT_SECRET_KEY
)

# SECURITY WARNING: don't run with debug turned on in production!
# Local default is DEBUG=True unless explicitly overridden.
_debug_env = os.environ.get('DEBUG')
if _debug_env is None:
    DEBUG = not (os.environ.get('VERCEL') == '1' or os.environ.get('PROD') == '1')
else:
    DEBUG = _debug_env.strip().lower() in ('1', 'true', 'yes', 'on')

# Warn loudly if still using the insecure default in production.
# Does NOT crash the app — set SECRET_KEY (or DJANGO_SECRET_KEY / SECRET_KEY_BASE) in Vercel env vars.
if not DEBUG and (not SECRET_KEY or SECRET_KEY == DEFAULT_SECRET_KEY or SECRET_KEY.startswith('django-insecure')):
    import logging as _log
    _log.getLogger('django.security').critical(
        '⚠️  SECURITY RISK: SECRET_KEY is using the insecure default! '
        'Set SECRET_KEY (or DJANGO_SECRET_KEY / SECRET_KEY_BASE) in your Vercel/Railway env vars immediately.'
    )

# OpenAI Configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# Google Gemini Configuration
# Set AI_PROVIDER=gemini to make Gemini the primary provider.
# Supported models: gemini-2.5-flash, gemini-2.5-pro
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
GEMINI_MODEL   = os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash')
AI_PROVIDER    = os.environ.get('AI_PROVIDER', 'openai')  # 'openai' | 'gemini'

# Paystack Payment Gateway
PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY', '')
PAYSTACK_PUBLIC_KEY = os.environ.get('PAYSTACK_PUBLIC_KEY', '')
# Currency code sent to Paystack (GHS, NGN, KES, USD …)
PAYSTACK_CURRENCY  = os.environ.get('PAYSTACK_CURRENCY', 'GHS')

# Africa's Talking SMS & WhatsApp
AFRICASTALKING_USERNAME = os.environ.get('AFRICASTALKING_USERNAME') or os.environ.get('AT_USERNAME', 'sandbox')
AFRICASTALKING_API_KEY  = os.environ.get('AFRICASTALKING_API_KEY') or os.environ.get('AT_API_KEY', '')
AT_WHATSAPP_PRODUCT_ID  = os.environ.get('AT_WHATSAPP_PRODUCT_ID', '')

# Web Push / VAPID Configuration
# Generate new keys: python -c "from py_vapid import Vapid; v=Vapid(); v.generate_keys(); ..."
VAPID_PUBLIC_KEY = os.environ.get(
    'VAPID_PUBLIC_KEY',
    'BKuDGCc0mEhuW5kDr-xnrZ2CLSMHv6po1vhtrbFnMEBhJNJhiqsHYWkNsrEDmlXsJNQ_4fbjX8gewbwfqconYVo'
)
VAPID_PRIVATE_KEY_PEM = os.environ.get('VAPID_PRIVATE_KEY_PEM', '')
if VAPID_PRIVATE_KEY_PEM:
    VAPID_PRIVATE_KEY_PEM = VAPID_PRIVATE_KEY_PEM.replace('\\n', '\n')  # env vars store literal \n — convert to real newlines
VAPID_CLAIMS = {'sub': os.environ.get('VAPID_ADMIN_EMAIL', 'mailto:admin@schoolportal.app')}

# =====================
# ALLOWED HOSTS & CSRF
# =====================
_allowed = os.environ.get('ALLOWED_HOSTS', '')
if _allowed:
    ALLOWED_HOSTS = [h.strip() for h in _allowed.split(',') if h.strip()]
elif DEBUG:
    ALLOWED_HOSTS = ['*']
else:
    # Production fallback: allow common deployment hosts
    ALLOWED_HOSTS = [
        'localhost', '127.0.0.1',
        '.vercel.app', '.railway.app',
        '.onrender.com', '.herokuapp.com',
    ]

# CSRF Trusted Origins
CSRF_TRUSTED_ORIGINS = [
    'https://*.railway.app',
    'https://*.vercel.app',
    'https://school-portal-inky.vercel.app',
]

# =====================
# SITE URL (for absolute links in emails)
# =====================
# Set SITE_URL in your .env / production environment
# e.g. SITE_URL=https://school-portal-inky.vercel.app
SITE_URL = os.environ.get('SITE_URL', 'https://school-portal-saas.vercel.app').rstrip('/')

# Application definition

SHARED_APPS = [
    'django_tenants',

    # Shared administrative + auth apps (Needed for Public Schema Admin)
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # 'tenants' MUST come after django.contrib.auth so TenantsConfig.ready()
    # runs after AuthConfig.ready() and can successfully disconnect/replace
    # the create_permissions post_migrate handler with the ignore_conflicts version.
    'tenants',
    
    # Third party shared
    'cloudinary_storage',
    'cloudinary',
    'crispy_forms',
    'crispy_bootstrap5',
    
    # Local apps that need to exist in public schema (e.g. for superuser)
    'accounts',
    'individual_users',
]

# Conditionally add rest_framework if installed
try:
    import rest_framework  # noqa: F401
    SHARED_APPS.insert(-1, 'rest_framework')
except ImportError:
    pass

TENANT_APPS = [
    # Django apps that need to be isolated per tenant
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # Third party apps in tenant context
    'crispy_forms',
    'crispy_bootstrap5',

    # Local apps that need to be isolated per tenant
    'accounts',
    'students',
    'teachers',
    'academics',
    'parents',
    'announcements',
    'finance',
    'communication',
    'homework',
]

INSTALLED_APPS = list(SHARED_APPS) + [app for app in TENANT_APPS if app not in SHARED_APPS]

TENANT_MODEL = "tenants.School"
TENANT_DOMAIN_MODEL = "tenants.Domain"
PUBLIC_SCHEMA_NAME = "public"

DATABASE_ROUTERS = (
    'django_tenants.routers.TenantSyncRouter',
)

MIDDLEWARE = [
    #'django_tenants.middleware.main.TenantMainMiddleware',  # Disabled for Path Strategy
    'tenants.middleware.TenantPathMiddleware', # Custom Path-based Routing
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'accounts.middleware.OnboardingAutoMarkMiddleware',
]

ROOT_URLCONF = 'school_system.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'academics.context_processors.school_info',
                'announcements.context_processors.user_notifications',
                'teachers.context_processors.teacher_context',
                'tenants.context_processors.trial_status',
                'accounts.context_processors.onboarding_context',
                'individual_users.context_processors.individual_credits',
            ],
            'string_if_invalid': '',  # Return empty string instead of raising errors for undefined variables
        },
    },
]

WSGI_APPLICATION = 'school_system.wsgi.application'


# =====================
# DATABASE CONFIGURATION - FIXED
# =====================
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # Production / Neon Database
    db_cfg = dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=600,
        engine='school_system.db_backend',  # Custom backend with retry logic
    )
    # ATOMIC_REQUESTS=True is critical for pgBouncer transaction mode (Neon):
    # pgBouncer may assign a different physical PostgreSQL server connection for each
    # transaction (statement) in autocommit mode.  SET search_path is session-scoped,
    # so a fresh server connection has search_path=public.  With ATOMIC_REQUESTS=True,
    # Django wraps every view in a single BEGIN/COMMIT transaction.  pgBouncer holds
    # ONE server connection for the entire transaction, so all queries in the view
    # see the correct search_path set at transaction start.
    #
    # NOTE: ATOMIC_REQUESTS only covers the view — middleware (including
    # AuthenticationMiddleware's User lookup) runs in autocommit mode.
    # TenantPathMiddleware.process_view wraps the first request.user access
    # in transaction.atomic() to keep SET search_path + SELECT on one
    # pgBouncer server connection.  Any NEW middleware or code that runs
    # tenant-scoped DB queries outside a view MUST also use
    # transaction.atomic() for the same reason.
    db_cfg['ATOMIC_REQUESTS'] = True

    # On serverless (Vercel) keep connections short to avoid "connection already closed" reuse
    if os.environ.get('VERCEL') == '1':
        db_cfg['CONN_MAX_AGE'] = 0
        db_cfg['CONN_HEALTH_CHECKS'] = True
    else:
        # Non-serverless: reuse connections to avoid repeated SSL handshakes (~300-500ms each)
        db_cfg['CONN_MAX_AGE'] = 60
        db_cfg['CONN_HEALTH_CHECKS'] = True

    # Neon-friendly keepalive / timeouts to avoid stale connections on serverless
    db_cfg.setdefault('OPTIONS', {})
    db_cfg['OPTIONS'].update({
        'connect_timeout': 10,
        'keepalives': 1,
        'keepalives_idle': 20,
        'keepalives_interval': 20,
        'keepalives_count': 3,
    })
    DATABASES = {'default': db_cfg}
else:
    # Local development: Must use PostgreSQL for django-tenants
    # SQLite is NOT supported
    DATABASES = {
        'default': {
            'ENGINE': 'django_tenants.postgresql_backend',
            'NAME': 'school_db_local',
            'USER': 'postgres',
            'PASSWORD': 'password',
            'HOST': 'localhost',
            'PORT': '5432',
        }
    }


# =====================
# CACHING
# =====================
_REDIS_URL = os.environ.get('REDIS_URL')
if _REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': _REDIS_URL,
            'TIMEOUT': 300,
            'KEY_PREFIX': 'padi',
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'padi-cache',
            'TIMEOUT': 300,
        }
    }


# =====================
# DJANGO-TENANTS PERFORMANCE
# =====================
# Limit SET search_path to once per request (not on every cursor call).
# pgBouncer transaction mode (Neon) can silently swap the physical PostgreSQL
# server connection between autocommit statements.  SET search_path is
# session-scoped, so a fresh server connection resets to search_path=public.
#
# With TENANT_LIMIT_SET_CALLS=True, django-tenants caches whether SET was
# already issued and SKIPS it on subsequent cursors.  This is UNSAFE with
# pgBouncer: the middleware issues SET on cursor 1 (connection A), then
# AuthenticationMiddleware opens cursor 2, which may hit connection B (fresh,
# search_path=public).  Because the cache says "already set," SET is skipped
# and the User query hits the public schema → user not found → AnonymousUser.
#
# Setting False forces SET search_path on EVERY cursor.  With ATOMIC_REQUESTS
# the view's queries all share one transaction (= one pgBouncer connection),
# so the cost is just one extra SET per cursor in the 2-3 autocommit
# middleware queries — negligible compared to Neon network latency.
TENANT_LIMIT_SET_CALLS = False


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
LANGUAGE_CODE = 'en'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

from django.utils.translation import gettext_lazy as _
LANGUAGES = [
    ('en', _('English')),
    ('fr', _('Français')),
    ('tw', _('Twi')),
]
LOCALE_PATHS = [BASE_DIR / 'locale']


# =====================
# STATIC & MEDIA FILES
# =====================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# In Vercel, static files are handled by CDN, so don't set STATIC_ROOT
# In other environments, use staticfiles directory for collectstatic
if os.environ.get('VERCEL') != '1':
    STATIC_ROOT = BASE_DIR / 'staticfiles'
else:
    STATIC_ROOT = None

# WhiteNoise for serving static files in production
# Use simple Compressed storage to avoid 500 errors if manifest is missing
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# Serve static files directly from app/static directories in environments
# where collected static artifacts may be unavailable (local + Vercel).
# This keeps Django admin CSS/JS available at /static/admin/*.
if DEBUG or os.environ.get('VERCEL') == '1':
    WHITENOISE_USE_FINDERS = True

# Ensure STATIC_ROOT exists so WhiteNoise doesn't warn on every cold start.
# Vercel's /var/task/ is read-only at runtime, so skip for Vercel
if STATIC_ROOT and os.environ.get('VERCEL') != '1':
    try:
        STATIC_ROOT.mkdir(exist_ok=True)
    except OSError:
        pass


# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Cloudinary cloud name (always available for upload widget)
CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME', '')

# Cloudinary Storage Configuration
# Only use Cloudinary in production/Vercel environment
if os.environ.get('VERCEL') == '1' or os.environ.get('PROD') == '1':
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    
    # Cloudinary Config
    CLOUDINARY_STORAGE = {
        'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
        'API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
        'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET'),
    }


# =====================
# AUTH & LOGIN
# =====================
AUTH_USER_MODEL = 'accounts.User'
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'individual_users.backends.EmailOrPhoneBackend',
]

GOOGLE_OAUTH_CLIENT_ID = os.environ.get('GOOGLE_OAUTH_CLIENT_ID', '')
GOOGLE_OAUTH_CLIENT_SECRET = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET', '')

# =====================
# SCHOOL DOMAIN CONFIGURATION
# =====================
# Base domain for school subdomains (e.g., 'schoolportal.com' creates 'school1.schoolportal.com')
# For local development, set to 'local' for *.local domains
# For production, set via environment variable: BASE_SCHOOL_DOMAIN=yourdomain.com
BASE_SCHOOL_DOMAIN = os.environ.get('BASE_SCHOOL_DOMAIN', 'local')


# =====================
# CRISPY FORMS CONFIG
# =====================
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# =====================
# DJANGO REST FRAMEWORK
# =====================
try:
    import rest_framework  # noqa: F401
    REST_FRAMEWORK = {
        'DEFAULT_AUTHENTICATION_CLASSES': [
            'rest_framework.authentication.SessionAuthentication',
            'rest_framework.authentication.TokenAuthentication',
        ],
        'DEFAULT_PERMISSION_CLASSES': [
            'rest_framework.permissions.IsAuthenticated',
        ],
        'DEFAULT_THROTTLE_CLASSES': [
            'rest_framework.throttling.AnonRateThrottle',
            'rest_framework.throttling.UserRateThrottle',
        ],
        'DEFAULT_THROTTLE_RATES': {
            'anon': '30/minute',
            'user': '120/minute',
        },
        'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
        'PAGE_SIZE': 50,
    }
except ImportError:
    pass


# =====================
# DEFAULT SETTINGS
# =====================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Allow larger request bodies for image-based AI scanning (base64 payloads).
# Django default is 2.5 MB; camera photos encoded as base64 can reach ~8-12 MB.
DATA_UPLOAD_MAX_MEMORY_SIZE = 15 * 1024 * 1024  # 15 MB

# =====================
# EMAIL CONFIGURATION (Brevo/SMTP)
# =====================
# For local testing, set EMAIL_BACKEND_TYPE='console' if you want to see emails in terminal
# Otherwise, it attempts to send real emails via SMTP
if os.environ.get('EMAIL_BACKEND_TYPE') == 'console':
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp-relay.brevo.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'School Admin <noreply@school.com>')

# =====================
# SESSION PERSISTENCE
# =====================
# Uses Django's built-in signed-cookie session backend.  The entire session
# is stored client-side in a signed (HMAC'd) cookie — no DB lookup needed,
# so there is no schema-switching problem in multi-tenant path-based routing.
#
# SESSION_COOKIE_NAME is set to '_sp_session' (not the default 'sessionid').
# This ensures old DB-session cookies from any previous backend change are
# ignored — they have a different name so the browser never sends them.
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'

# Unique cookie name — avoids collisions with any previously set cookies
# from earlier session-engine experiments (DB backend etc.)
SESSION_COOKIE_NAME = '_sp_session'

# Rolling 1-year expiry — tenant admin accounts use this maximum;
# regular users who uncheck "Keep me logged in" get set_expiry(0)
# (browser-session cookie) which overrides this per-session.
SESSION_COOKIE_AGE = 365 * 24 * 60 * 60  # 1 year in seconds

# Re-send the cookie on every response so the 30-day window is always rolling.
SESSION_SAVE_EVERY_REQUEST = True

# Cookie flags
SESSION_COOKIE_HTTPONLY = True    # block JS access (XSS protection)
SESSION_COOKIE_SAMESITE = 'Lax'  # prevent cross-site request leakage

# Only force secure cookies when running behind a known HTTPS platform
# (Vercel/Railway) or when explicitly requested via env var.
_running_on_hosted_https = bool(
    os.environ.get('VERCEL')
    or os.environ.get('RAILWAY_ENVIRONMENT')
    or os.environ.get('RAILWAY_ENVIRONMENT_NAME')
    or os.environ.get('RAILWAY_PROJECT_ID')
)
_force_secure_cookies = os.environ.get('FORCE_SECURE_COOKIES', '').lower() in ('1', 'true', 'yes', 'on')
_use_secure_cookies = (not DEBUG) and (_running_on_hosted_https or _force_secure_cookies)

SESSION_COOKIE_SECURE = _use_secure_cookies
CSRF_COOKIE_SECURE = _use_secure_cookies

# Explicit: cookie is valid for the exact request domain only.
# With path-based multi-tenancy (/{school}/), all tenants share a single
# domain, so the default (None → current host) is correct.
SESSION_COOKIE_DOMAIN = None

# =====================
# VERCEL / PRODUCTION SECURITY
# =====================
# Trust X-Forwarded-Proto header from Vercel / Railway reverse proxy
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

if not DEBUG:
    # Security headers
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
# =====================
# ERROR HANDLER CONFIGURATION
# =====================
# Custom error page handlers with modern design
# These will be used when DEBUG = False and exceptions occur
ERROR_400_FILE = os.path.join(BASE_DIR, 'templates', '400.html')
ERROR_403_FILE = os.path.join(BASE_DIR, 'templates', '403.html')
ERROR_404_FILE = os.path.join(BASE_DIR, 'templates', '404.html')
ERROR_500_FILE = os.path.join(BASE_DIR, 'templates', '500.html')
ERROR_503_FILE = os.path.join(BASE_DIR, 'templates', '503.html')

# Error handler views in urls.py will handle these
HANDLER400 = 'school_system.views.bad_request_400'
HANDLER403 = 'school_system.views.forbidden_403'
HANDLER404 = 'school_system.views.page_not_found_404'
HANDLER500 = 'school_system.views.server_error_500'

# =====================
# SENTRY ERROR TRACKING
# =====================
_SENTRY_DSN = os.environ.get('SENTRY_DSN', '')
if _SENTRY_DSN:
    import sentry_sdk
    sentry_sdk.init(
        dsn=_SENTRY_DSN,
        traces_sample_rate=float(os.environ.get('SENTRY_TRACES_RATE', '0.1')),
        profiles_sample_rate=float(os.environ.get('SENTRY_PROFILES_RATE', '0.1')),
        send_default_pii=False,
        environment=os.environ.get('SENTRY_ENVIRONMENT', 'production'),
    )

# =====================
# LOGGING
# =====================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}