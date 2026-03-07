from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from accounts import views as account_views
from accounts.views import TenantPasswordResetView
from tenants import views as tenant_views
import os
from django.http import FileResponse, Http404


def sw_view(request):
    """Serve sw.js from the root path with Service-Worker-Allowed: / header."""
    # Try static source first, then staticfiles dir
    candidates = [
        os.path.join(settings.BASE_DIR, 'static', 'sw.js'),
        os.path.join(settings.BASE_DIR, 'staticfiles', 'sw.js'),
    ]
    for path_candidate in candidates:
        if os.path.exists(path_candidate):
            response = FileResponse(open(path_candidate, 'rb'), content_type='application/javascript')
            response['Service-Worker-Allowed'] = '/'
            response['Cache-Control'] = 'no-cache'
            return response
    raise Http404('sw.js not found')

admin.site.site_header = "School Portal Administration"
admin.site.site_title = "School Admin"
admin.site.index_title = "Welcome to School Management System"


urlpatterns = [
    # Favicon — serve before tenant middleware can intercept
    path('favicon.ico', RedirectView.as_view(url='/static/img/logo.png', permanent=True)),
    path('favicon.png', RedirectView.as_view(url='/static/img/logo.png', permanent=True)),
    path('sw.js', sw_view, name='sw'),
    path('admin/', admin.site.urls),
    path('', account_views.homepage, name='home'),
    path('find-school/', account_views.find_school, name='find_school'),
    path('signup/', tenant_views.school_signup, name='signup'),
    path('login/', account_views.login_view, name='login'),
    # path('home/', account_views.homepage, name='home'), # Redirect old home
    path('logout/', account_views.logout_view, name='logout'),
    path('dashboard/', account_views.dashboard, name='dashboard'),
    path('password/change/', auth_views.PasswordChangeView.as_view(
        template_name='accounts/password_change.html',
        success_url='/password/change/done/'
    ), name='password_change'),
    path('password/change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='accounts/password_change_done.html'
    ), name='password_change_done'),

    # Password Reset
    path('password_reset/', TenantPasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'
    ), name='password_reset_complete'),

    path('accounts/', include('accounts.urls')),
    path('teachers/', include('teachers.urls')),
    path('students/', include('students.urls')),
    path('parents/', include('parents.urls')),
    path('homework/', include('homework.urls')),
    path('academics/', include('academics.urls')),
    path('announcements/', include('announcements.urls')),
    path('communication/', include('communication.urls')),
    path('finance/', include('finance.urls')),
    path('tenants/', include('tenants.urls')),
    path('i18n/', include('django.conf.urls.i18n')),  # Language switcher
    # path('debug/migrate/', account_views.debug_migrate, name='debug_migrate'),
    path('debug/status/', account_views.debug_status, name='debug_status'),
    path('debug/session/', account_views.session_debug, name='session_debug'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)