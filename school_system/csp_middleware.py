"""Content-Security-Policy middleware.

NOTE: Nonce injection is disabled because the CSP spec dictates that
'unsafe-inline' is ignored when a nonce or hash is present.  Bootstrap,
third-party libraries, and many templates apply inline styles / event
handlers that cannot be nonced, so the nonce was breaking the entire UI.
Re-enable nonce injection only after *all* inline styles and scripts
have been migrated to external files or explicitly nonced.
"""

import secrets

from django.conf import settings


class CSPMiddleware:
    """Adds a Content-Security-Policy header (no nonce for now)."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.csp_template = getattr(settings, 'CSP_HEADER', '')

    def __call__(self, request):
        # Keep a nonce on the request so templates can start adopting it
        # progressively, but do NOT inject it into the header yet.
        nonce = secrets.token_urlsafe(32)
        request.csp_nonce = nonce

        response = self.get_response(request)

        if self.csp_template and 'Content-Security-Policy' not in response:
            response['Content-Security-Policy'] = self.csp_template
        return response
