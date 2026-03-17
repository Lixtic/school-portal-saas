from django import template
import datetime

register = template.Library()

@register.filter
def subtract(value, arg):
    """Subtract arg from value. Usage: {{ amount_payable|subtract:total_paid_amount }}"""
    try:
        return value - arg
    except (TypeError, ValueError):
        return ''

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def get_lesson_at(entries, start_time_str):
    """
    Returns the entry that matches the given start_time string (HH:MM).
    Usage: {{ entry_list|get_lesson_at:"07:00" }}
    """
    if not entries:
        return None
    
    for entry in entries:
        # Check if entry.start_time matches the string
        # entry.start_time is a datetime.time object
        if entry.start_time.strftime("%H:%M") == start_time_str:
            return entry
    return None

