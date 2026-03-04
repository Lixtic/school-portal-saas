from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('users/', views.manage_users, name='manage_users'),
    path('users/<int:user_id>/reset-password/', views.admin_password_reset, name='admin_password_reset'),
    path('analytics/', views.school_analytics, name='school_analytics'),
]
