from django import template

register = template.Library()

@register.filter
def safe_attr(obj, attr_name):
    """Safely get attribute from object with fallback to empty string"""
    if obj is None:
        return ''
    try:
        value = getattr(obj, attr_name, '')
        return value if value is not None else ''
    except:
        return ''

@register.filter
def safe_attr_with_default(obj, args):
    """Safely get attribute with custom default. Usage: {{ obj|safe_attr_with_default:'attr_name,default_value' }}"""
    if obj is None:
        return args.split(',', 1)[1] if ',' in args else ''
    try:
        parts = args.split(',', 1)
        attr_name = parts[0]
        default = parts[1] if len(parts) > 1 else ''
        value = getattr(obj, attr_name, default)
        return value if value is not None else default
    except:
        return parts[1] if len(parts) > 1 else ''
