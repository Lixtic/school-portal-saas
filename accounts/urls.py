from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('users/', views.manage_users, name='manage_users'),
    path('users/<int:user_id>/reset-password/', views.admin_password_reset, name='admin_password_reset'),
    path('users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    path('analytics/', views.school_analytics, name='school_analytics'),
    path('settings/', views.user_settings, name='user_settings'),
    # Onboarding
    path('onboarding/dismiss/', views.onboarding_dismiss, name='onboarding_dismiss'),
    path('onboarding/complete-step/', views.onboarding_complete_step, name='onboarding_complete_step'),
]
