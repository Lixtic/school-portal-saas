"""Lightweight rate-limiting decorator using Django's cache framework.

Usage:
    from school_system.ratelimit import ratelimit

    @ratelimit(key='ip', rate='5/m')    # 5 requests per minute per IP
    @ratelimit(key='ip', rate='20/h')   # 20 requests per hour per IP
    def my_view(request):
        ...
"""

import functools
import hashlib

from django.core.cache import cache
from django.http import JsonResponse


def _parse_rate(rate_str):
    """Parse '5/m', '20/h', '100/d' into (count, seconds)."""
    count, period = rate_str.split('/')
    count = int(count)
    multipliers = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
    seconds = multipliers.get(period[0].lower(), 60)
    return count, seconds


def _get_client_ip(request):
    """Extract client IP, respecting X-Forwarded-For from reverse proxies."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


def ratelimit(key='ip', rate='10/m', method=None, block=True):
    """Decorator that rate-limits a view.

    Args:
        key: 'ip' (default) or 'user' (requires authentication).
        rate: 'N/period' where period is s/m/h/d.
        method: Limit only specific HTTP methods (e.g. 'POST'). None = all.
        block: If True, return 429 response. If False, set request.limited = True.
    """
    max_requests, window = _parse_rate(rate)

    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Skip rate limiting for specific methods if configured
            if method and request.method != method.upper():
                return view_func(request, *args, **kwargs)

            # Build cache key
            if key == 'user' and hasattr(request, 'user') and request.user.is_authenticated:
                ident = str(request.user.pk)
            else:
                ident = _get_client_ip(request)

            path_hash = hashlib.md5(
                request.path.encode(), usedforsecurity=False,
            ).hexdigest()[:8]
            cache_key = f'rl:{path_hash}:{ident}'

            # Check and increment
            current = cache.get(cache_key, 0)
            if current >= max_requests:
                if block:
                    return JsonResponse(
                        {'error': 'Too many requests. Please try again later.'},
                        status=429,
                    )
                request.limited = True
            else:
                # Increment with TTL
                try:
                    cache.incr(cache_key)
                except ValueError:
                    cache.set(cache_key, 1, window)

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
