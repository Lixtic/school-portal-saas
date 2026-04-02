from django.urls import path
from individual_users import views

app_name = 'individual'

urlpatterns = [
    # Auth
    path('signup/', views.signup_view, name='signup'),
    path('signin/', views.signin_view, name='signin'),
    path('auth/google/', views.google_auth_view, name='google_auth'),
    path('signout/', views.signout_view, name='signout'),

    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Addon marketplace
    path('addons/', views.addons_view, name='addons'),
    path('addons/subscribe/', views.subscribe_addon, name='subscribe_addon'),
    path('addons/unsubscribe/', views.unsubscribe_addon, name='unsubscribe_addon'),

    # API keys
    path('api-keys/', views.api_keys_view, name='api_keys'),
    path('api-keys/revoke/', views.revoke_api_key, name='revoke_api_key'),

    # API status endpoint
    path('api/status/', views.api_status, name='api_status'),
]
