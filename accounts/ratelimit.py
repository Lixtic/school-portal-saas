"""
Cache-based rate limiter for Django views (no external packages).
Uses the same cache backend configured in settings (Redis in prod, LocMemCache in dev).
"""
import functools
import logging

from django.core.cache import cache
from django.http import JsonResponse

logger = logging.getLogger(__name__)

# Default limits
LOGIN_MAX_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 300  # 5 minutes


def _get_client_ip(request):
    """Extract client IP, respecting X-Forwarded-For behind proxies."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


def rate_limit_login(view_func):
    """
    Decorator that blocks login attempts after LOGIN_MAX_ATTEMPTS failures
    within LOGIN_WINDOW_SECONDS per IP address.

    Only counts POST requests (actual login attempts).
    Resets the counter on successful login.
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.method != 'POST':
            return view_func(request, *args, **kwargs)

        ip = _get_client_ip(request)
        cache_key = f'login_attempts_{ip}'
        attempts = cache.get(cache_key, 0)

        if attempts >= LOGIN_MAX_ATTEMPTS:
            logger.warning('Rate limit exceeded for login from IP %s', ip)
            from django.contrib import messages
            messages.error(
                request,
                'Too many login attempts. Please wait a few minutes before trying again.',
            )
            from django.shortcuts import render
            return render(request, 'accounts/login.html', {
                'next': request.GET.get('next', ''),
                'rate_limited': True,
            }, status=429)

        response = view_func(request, *args, **kwargs)

        # If login failed (re-renders login page with status 200), increment counter.
        # Successful login returns a 302 redirect.
        if response.status_code != 302:
            cache.set(cache_key, attempts + 1, LOGIN_WINDOW_SECONDS)
        else:
            # Successful login — clear the counter
            cache.delete(cache_key)

        return response

    return wrapper
