"""Content-Security-Policy middleware — lightweight, no extra dependencies."""

from django.conf import settings


class CSPMiddleware:
    """Adds a Content-Security-Policy header to every response."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.csp_header = getattr(settings, 'CSP_HEADER', '')

    def __call__(self, request):
        response = self.get_response(request)
        if self.csp_header and 'Content-Security-Policy' not in response:
            response['Content-Security-Policy'] = self.csp_header
        return response
