"""Content-Security-Policy middleware with per-request nonce support."""

import secrets

from django.conf import settings


class CSPMiddleware:
    """Adds a Content-Security-Policy header with a per-request nonce."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.csp_template = getattr(settings, 'CSP_HEADER', '')

    def __call__(self, request):
        # Generate a cryptographically random nonce for this request
        nonce = secrets.token_urlsafe(32)
        request.csp_nonce = nonce

        response = self.get_response(request)

        if self.csp_template and 'Content-Security-Policy' not in response:
            # Inject nonce into script-src and style-src directives
            csp = self.csp_template.replace(
                "script-src 'self' 'unsafe-inline'",
                f"script-src 'self' 'unsafe-inline' 'nonce-{nonce}'",
            ).replace(
                "style-src 'self' 'unsafe-inline'",
                f"style-src 'self' 'unsafe-inline' 'nonce-{nonce}'",
            )
            response['Content-Security-Policy'] = csp
        return response
