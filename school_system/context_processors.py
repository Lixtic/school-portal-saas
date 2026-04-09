def csp_nonce(request):
    """Make the CSP nonce available in templates as {{ csp_nonce }}."""
    return {'csp_nonce': getattr(request, 'csp_nonce', '')}
