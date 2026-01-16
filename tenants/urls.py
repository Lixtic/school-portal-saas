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
]
