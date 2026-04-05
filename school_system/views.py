"""
Error handler views for SchoolPadi
Handles custom 400, 403, 404, and 500 error pages
"""

from django.shortcuts import render
from django.views.decorators.http import require_http_methods


def bad_request_400(request, exception=None):
    """
    Handle 400 Bad Request errors
    """
    return render(
        request,
        '400.html',
        status=400,
        context={
            'error_code': 400,
            'error_title': 'Bad Request',
        }
    )


def forbidden_403(request, exception=None):
    """
    Handle 403 Forbidden errors
    """
    return render(
        request,
        '403.html',
        status=403,
        context={
            'error_code': 403,
            'error_title': 'Access Denied',
        }
    )


def page_not_found_404(request, exception=None):
    """
    Handle 404 Not Found errors
    """
    return render(
        request,
        '404.html',
        status=404,
        context={
            'error_code': 404,
            'error_title': 'Page Not Found',
            'requested_path': request.path,
        }
    )


def server_error_500(request):
    """
    Handle 500 Internal Server Error
    """
    return render(
        request,
        '500.html',
        status=500,
        context={
            'error_code': 500,
            'error_title': 'Internal Server Error',
        }
    )
