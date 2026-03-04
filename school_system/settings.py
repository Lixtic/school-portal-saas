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

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-your-secret-key-here-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
# Defaults to False unless explicitly set. Use DEBUG=True in local .env
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# Warn (but don't crash) if SECRET_KEY is still the default in production
if not DEBUG and SECRET_KEY.startswith('django-insecure'):
    import logging as _log
    _log.getLogger('django.security').critical(
        "SECRET_KEY is using the insecure default! Set a proper SECRET_KEY env var."
    )

# OpenAI Configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# Web Push / VAPID Configuration
# Generate new keys: python -c "from py_vapid import Vapid; v=Vapid(); v.generate_keys(); ..."
VAPID_PUBLIC_KEY = os.environ.get(
    'VAPID_PUBLIC_KEY',
    'BKuDGCc0mEhuW5kDr-xnrZ2CLSMHv6po1vhtrbFnMEBhJNJhiqsHYWkNsrEDmlXsJNQ_4fbjX8gewbwfqconYVo'
)
VAPID_PRIVATE_KEY_PEM = os.environ.get(
    'VAPID_PRIVATE_KEY_PEM',
    '-----BEGIN PRIVATE KEY-----\nMIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgPjsGsJ/jLvM00vUZ\nYvsTepEUiwFt+2UpV+q9RLg43mOhRANCAASrgxgnNJhIbluZA6/sZ62dgi0jB7+q\naNb4ba2xZzBAYSTSYYqrB2FpDbKxA5pV7CTUP+H241/IHsG8H6nKJ2Fa\n-----END PRIVATE KEY-----'
)
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
SITE_URL = os.environ.get('SITE_URL', 'http://localhost:8000').rstrip('/')

# Application definition

SHARED_APPS = [
    'django_tenants',
    'tenants',
    
    # Shared administrative + auth apps (Needed for Public Schema Admin)
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    
    # Third party shared
    'cloudinary_storage',
    'cloudinary',
    'crispy_forms',
    'crispy_bootstrap5',
    
    # Local apps that need to exist in public schema (e.g. for superuser)
    'accounts', 
]

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
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
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
    # On serverless (Vercel) keep connections short to avoid "connection already closed" reuse
    if os.environ.get('VERCEL') == '1':
        db_cfg['CONN_MAX_AGE'] = 0
        db_cfg['CONN_HEALTH_CHECKS'] = True
    else:
        # Fallback for other prod hosts: prefer short-lived connections to avoid stale sockets
        db_cfg['CONN_MAX_AGE'] = 0
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


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# =====================
# STATIC & MEDIA FILES
# =====================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise for serving static files in production
# Use simple Compressed storage to avoid 500 errors if manifest is missing
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'


# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

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
# DEFAULT SETTINGS
# =====================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

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
# SESSION PERSISTENCE (critical for serverless / Vercel)
# =====================
# Save session on every request so the cookie is always refreshed.
# Without this, serverless cold starts can lose sessions when the
# session is not explicitly modified by the view.
SESSION_SAVE_EVERY_REQUEST = True

# =====================
# VERCEL / PRODUCTION SECURITY
# =====================
# Trust X-Forwarded-Proto header from Vercel / Railway reverse proxy
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

if not DEBUG:
    # Security headers
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

    # NOTE: SECURE_SSL_REDIRECT, SESSION_COOKIE_SECURE, and
    # CSRF_COOKIE_SECURE are intentionally NOT set here.
    # Vercel / Railway handle HTTPS at the edge layer.
    # Setting these flags in Django's WSGI layer (which receives
    # internal HTTP from the reverse proxy) causes session loss.
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