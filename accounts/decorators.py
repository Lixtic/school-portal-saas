from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

def admin_required(function=None):
    """
    Decorator for views that checks that the user is an admin.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_active and (u.is_superuser or u.user_type == 'admin'),
        login_url='login',
        redirect_field_name=None
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def teacher_required(function=None):
    """
    Decorator for views that checks that the user is a teacher.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.user_type == 'teacher',
        login_url='login',
        redirect_field_name=None
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def student_required(function=None):
    """
    Decorator for views that checks that the user is a student.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.user_type == 'student',
        login_url='login',
        redirect_field_name=None
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def parent_required(function=None):
    """
    Decorator for views that checks that the user is a parent.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.user_type == 'parent',
        login_url='login',
        redirect_field_name=None
    )
    if function:
        return actual_decorator(function)
    return actual_decorator
