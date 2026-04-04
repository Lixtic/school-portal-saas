from django.urls import path
from . import views

app_name = 'tenants'

urlpatterns = [
    path('setup/', views.school_setup_wizard, name='setup_wizard'),
    path('', views.landlord_landing, name='landlord_landing'),
    path('landlord/', views.landlord_redirect, name='landlord_dashboard'),
    path('landlord/landing-template/', views.landing_template_picker, name='landing_template_picker'),
    path('landlord/ai-models/', views.ai_model_settings, name='ai_model_settings'),
    path('landlord/addon-pricing/', views.addon_pricing_management, name='addon_pricing'),
    path('landlord/credit-packs/', views.credit_pack_pricing, name='credit_pack_pricing'),
    
    # Super Admin: Direct school creation
    path('superadmin/create-school/', views.superadmin_create_school, name='superadmin_create_school'),
    
    path('approval-queue/', views.approval_queue, name='approval_queue'),
    path('approval-queue/count/', views.approval_pending_count_api, name='approval_pending_count'),
    path('review/<int:school_id>/', views.review_school, name='review_school'),
    path('resend-credentials/<int:school_id>/', views.resend_school_credentials, name='resend_credentials'),
    path('revenue/', views.revenue_analytics, name='revenue_analytics'),
    path('marketplace/', views.addon_marketplace, name='addon_marketplace'),
    path('marketplace/purchase/<int:addon_id>/', views.purchase_addon, name='purchase_addon'),
    path('marketplace/verify/', views.marketplace_verify, name='marketplace_verify'),
    path('marketplace/webhook/', views.paystack_school_webhook, name='paystack_school_webhook'),
    path('marketplace/cancel/<int:addon_id>/', views.cancel_addon, name='cancel_addon'),
    
    # System Health & Support
    path('system-health/', views.system_health_dashboard, name='system_health'),
    path('support/', views.support_ticket_list, name='support_tickets'),
    path('support/<int:ticket_id>/', views.support_ticket_detail, name='support_ticket_detail'),
    path('support/create/', views.create_support_ticket, name='create_support_ticket'),
    path('backups/', views.database_backups, name='database_backups'),

    # Public application status check
    path('status/', views.application_status, name='application_status'),

    # Public pricing page
    path('pricing/', views.pricing_page, name='pricing'),

    # School subscription portal (tenant-admin)
    path('subscription/', views.school_subscription, name='school_subscription'),

    # Self-service plan upgrade via Paystack
    path('subscription/upgrade/', views.initiate_plan_upgrade, name='initiate_plan_upgrade'),
    path('subscription/upgrade/callback/', views.upgrade_plan_callback, name='upgrade_plan_callback'),

    # Landlord: activate / change a school's plan
    path('activate-plan/<int:school_id>/', views.activate_school_plan, name='activate_plan'),

    # Paystack webhook — platform-level (no tenant prefix needed)
    # Register this URL in the Paystack dashboard under Settings → Webhook URL
    path('paystack/webhook/', views.paystack_subscription_webhook, name='paystack_subscription_webhook'),
]
