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
# Default to True for local development, set to False in production
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# OpenAI Configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# =====================
# ALLOWED HOSTS & CSRF
# =====================
ALLOWED_HOSTS = ['*']  # Allow all hosts for now

# CSRF Trusted Origins
CSRF_TRUSTED_ORIGINS = [
    'https://*.railway.app',
    'https://*.vercel.app',
    'https://school-portal-inky.vercel.app',
]

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
        engine='django_tenants.postgresql_backend',
    )
    # On serverless (Vercel) keep connections short to avoid "connection already closed" reuse
    if os.environ.get('VERCEL') == '1':
        db_cfg['CONN_MAX_AGE'] = 0
        db_cfg['CONN_HEALTH_CHECKS'] = True
    else:
        # Fallback for other prod hosts: prefer short-lived connections to avoid stale sockets
        db_cfg['CONN_MAX_AGE'] = 0
        db_cfg['CONN_HEALTH_CHECKS'] = True
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
# VERCEL / PRODUCTION SECURITY
# =====================
# Always trust X-Forwarded-Proto header for Vercel
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
