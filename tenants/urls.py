from django.urls import path
from . import views

app_name = 'tenants'

urlpatterns = [
    path('setup/', views.school_setup_wizard, name='setup_wizard'),
    path('landlord/', views.landlord_dashboard, name='landlord_dashboard'),
    path('approval-queue/', views.approval_queue, name='approval_queue'),
    path('review/<int:school_id>/', views.review_school, name='review_school'),
    path('revenue/', views.revenue_analytics, name='revenue_analytics'),
    path('marketplace/', views.addon_marketplace, name='addon_marketplace'),
    path('marketplace/purchase/<int:addon_id>/', views.purchase_addon, name='purchase_addon'),
    path('marketplace/cancel/<int:addon_id>/', views.cancel_addon, name='cancel_addon'),
    
    # System Health & Support
    path('system-health/', views.system_health_dashboard, name='system_health'),
    path('support/', views.support_ticket_list, name='support_tickets'),
    path('support/<int:ticket_id>/', views.support_ticket_detail, name='support_ticket_detail'),
    path('support/create/', views.create_support_ticket, name='create_support_ticket'),
    path('backups/', views.database_backups, name='database_backups'),
]
