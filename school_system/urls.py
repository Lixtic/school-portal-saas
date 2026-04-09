from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView, TemplateView
from accounts import views as account_views
from accounts.views import TenantPasswordResetView
from tenants import views as tenant_views
from individual_users import seo_views
import os
from django.http import FileResponse, Http404
from individual_users.urls import teacher_urlpatterns


BLOG_POSTS = {
    'grade-management': {
        'title': 'How SchoolPadi Automates Grade Management',
        'template': 'blog/grade-management.html',
    },
    'fee-tracking': {
        'title': 'Real-Time Fee Tracking & Payment Management',
        'template': 'blog/fee-tracking.html',
    },
    'attendance-system': {
        'title': 'Attendance Tracking Made Visual',
        'template': 'blog/attendance-system.html',
    },
    'ai-engine': {
        'title': 'AI-Powered Tools for Educators',
        'template': 'blog/ai-engine.html',
    },
}


def blog_post_view(request, slug):
    from django.shortcuts import render
    post = BLOG_POSTS.get(slug)
    if not post:
        raise Http404
    return render(request, post['template'], {'post': post})


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

admin.site.site_header = "Django administration"
admin.site.site_title = "Django site admin"
admin.site.index_title = "Site administration"


urlpatterns = [
    # Favicon — serve before tenant middleware can intercept
    path('favicon.ico', RedirectView.as_view(url='/static/img/logo.png', permanent=True)),
    path('favicon.png', RedirectView.as_view(url='/static/img/logo.png', permanent=True)),
    path('apple-touch-icon.png', RedirectView.as_view(url='/static/img/logo.png', permanent=True)),
    path('apple-touch-icon-precomposed.png', RedirectView.as_view(url='/static/img/logo.png', permanent=True)),
    path('robots.txt', seo_views.robots_txt, name='robots_txt'),
    path('sitemap.xml', seo_views.sitemap_xml, name='sitemap_xml'),
    path('sitemap/', seo_views.visual_sitemap, name='sitemap'),
    path('sw.js', sw_view, name='sw'),
    path('offline/', TemplateView.as_view(template_name='offline.html'), name='offline'),
    path('about/', TemplateView.as_view(template_name='home/about.html'), name='about'),
    path('contact/', TemplateView.as_view(template_name='home/contact.html'), name='contact'),
    path('contact/submit/', account_views.contact_submit, name='contact_submit'),
    path('privacy/', TemplateView.as_view(template_name='home/privacy.html'), name='privacy'),
    path('terms/', TemplateView.as_view(template_name='home/terms.html'), name='terms'),
    # Blog
    path('blog/', TemplateView.as_view(template_name='blog/index.html'), name='blog_index'),
    path('blog/<slug:slug>/', blog_post_view, name='blog_post'),
    # SEO: city landing pages, comparison, and pricing alias
    path('schools-in/', account_views.city_index, name='city_index'),
    path('schools-in/<slug:city_slug>/', account_views.city_landing, name='city_landing'),
    path('compare/', TemplateView.as_view(template_name='home/compare.html'), name='compare'),
    path('pricing/', tenant_views.pricing_page, name='pricing'),
    path('admin/', admin.site.urls),
    path('pwa-launch/', account_views.pwa_launch, name='pwa_launch'),
    path('', account_views.homepage, name='home'),
    path('find-school/', account_views.find_school, name='find_school'),
    path('landlord/', tenant_views.landlord_dashboard, name='landlord_dashboard'),
    path('signup/', tenant_views.school_signup, name='signup'),
    path('get-started/', TemplateView.as_view(template_name='get_started.html'), name='get_started'),
    path('login/', account_views.login_view, name='login'),
    # path('home/', account_views.homepage, name='home'), # Redirect old home
    path('logout/', account_views.logout_view, name='logout'),
    path('dashboard/', account_views.dashboard, name='dashboard'),
    path('help/', RedirectView.as_view(pattern_name='academics:help_page', permanent=False), name='help_page_shortcut'),
    path('health/env/', account_views.env_health, name='env_health'),
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

    path('u/', include('individual_users.urls')),
    path('t/', include((teacher_urlpatterns, 'teacher'))),
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
    path('curriculum/', include('curriculum.urls')),
    path('i18n/', include('django.conf.urls.i18n')),  # Language switcher
]

# REST API (only if djangorestframework is installed)
try:
    import rest_framework  # noqa: F401
    urlpatterns.insert(0, path('api/', include('api.urls')))
except ImportError:
    pass

# Session diagnostic available in all environments (staff-only gate is in the view)
urlpatterns += [
    path('debug/session/', account_views.session_debug, name='session_debug'),
]

if settings.DEBUG:
    urlpatterns += [
        path('debug/status/', account_views.debug_status, name='debug_status'),
        path('debug/tenant-schema-health/', account_views.tenant_schema_health, name='tenant_schema_health'),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    if settings.STATIC_ROOT:
        urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error handlers
handler400 = 'accounts.views.error_400'
handler403 = 'accounts.views.error_403'
handler404 = 'accounts.views.error_404'
handler500 = 'accounts.views.error_500'