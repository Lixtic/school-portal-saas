from .models import SchoolInfo, AcademicYear
from django.db import connection
from django.conf import settings
from django.core.cache import cache

# SchoolInfo and AcademicYear are updated infrequently (once per term at most).
# Caching them per-tenant for 5 minutes saves 5+ DB round-trips per page.
_CACHE_TTL = 300  # 5 minutes


def _cache_key(prefix):
    """Return a per-tenant cache key so tenants never share cached data."""
    schema = getattr(connection, 'schema_name', 'public')
    return f'{prefix}_{schema}'


def school_info(request):
    current_academic_year = ''
    try:
        year_key = _cache_key('current_academic_year')
        current_year = cache.get(year_key)
        if current_year is None:
            current_year = (
                AcademicYear.objects.filter(is_current=True).first()
                or AcademicYear.objects.order_by('-start_date').first()
            )
            cache.set(year_key, current_year, _CACHE_TTL)
        if current_year:
            current_academic_year = current_year.name or ''
    except Exception:
        current_academic_year = ''

    try:
        info_key = _cache_key('school_info')
        info = cache.get(info_key)
        if info is None:
            info = SchoolInfo.objects.first()
            cache.set(info_key, info, _CACHE_TTL)
    except Exception:
        info = None
        
    if not info:
        # Check if we are in a tenant context
        tenant_name = "Portals"
        if hasattr(request, 'tenant') and request.tenant.schema_name != 'public':
            tenant_name = request.tenant.name

        # Return defaults if no DB entry yet
        return {
            'school_name': tenant_name,
            'school_address': None,
            'school_motto': None,
            'school_email': None,
            'school_phone': None,
            'school_info': None,
            'current_academic_year': current_academic_year,
            'vapid_public_key': getattr(settings, 'VAPID_PUBLIC_KEY', ''),
            'paystack_public_key': getattr(settings, 'PAYSTACK_PUBLIC_KEY', ''),
        }
    
    # Check if new fields exist in database
    def has_column(model, column_name):
        try:
            return column_name in [f.name for f in model._meta.get_fields()]
        except Exception:
            return False
    
    # Helper function to safely get attribute with default
    def safe_get(obj, attr, default=''):
        if not has_column(SchoolInfo, attr):
            return default
        try:
            value = getattr(obj, attr, default)
            return value if value is not None else default
        except Exception:
            return default
        
    base_context = {
        'school_name': info.name,
        'school_address': info.address,
        'school_phone': info.phone,
        'school_email': info.email,
        'school_motto': info.motto,
        'school_logo': info.logo,
        'school_info': info,
        'current_academic_year': current_academic_year,
        'vapid_public_key': getattr(settings, 'VAPID_PUBLIC_KEY', ''),
        'paystack_public_key': getattr(settings, 'PAYSTACK_PUBLIC_KEY', ''),
    }
    
    # Only add customization fields if they exist
    if has_column(SchoolInfo, 'hero_title'):
        base_context.update({
            'hero_title': safe_get(info, 'hero_title', info.name),
            'hero_subtitle': safe_get(info, 'hero_subtitle', info.motto),
            'cta_primary_text': safe_get(info, 'cta_primary_text', 'Portal Login'),
            'cta_primary_url': safe_get(info, 'cta_primary_url', '/login/'),
            'cta_secondary_text': safe_get(info, 'cta_secondary_text', 'Apply Now'),
            'cta_secondary_url': safe_get(info, 'cta_secondary_url', '/academics/apply/'),
            'feature1_title': safe_get(info, 'feature1_title', 'Academic Excellence'),
            'feature1_description': safe_get(info, 'feature1_description', 'Proven track record of outstanding academic performance.'),
            'feature1_icon': safe_get(info, 'feature1_icon', 'fa-award'),
            'feature2_title': safe_get(info, 'feature2_title', 'Expert Faculty'),
            'feature2_description': safe_get(info, 'feature2_description', 'Highly qualified and dedicated teachers.'),
            'feature2_icon': safe_get(info, 'feature2_icon', 'fa-users'),
            'feature3_title': safe_get(info, 'feature3_title', 'Modern Facilities'),
            'feature3_description': safe_get(info, 'feature3_description', 'State-of-the-art classrooms and laboratories.'),
            'feature3_icon': safe_get(info, 'feature3_icon', 'fa-building'),
            'show_stats_section': safe_get(info, 'show_stats_section', True),
            'show_programs_section': safe_get(info, 'show_programs_section', True),
            'show_gallery_preview': safe_get(info, 'show_gallery_preview', True),
        })
    
    return base_context
