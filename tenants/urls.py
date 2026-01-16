from django.urls import path
from . import views

app_name = 'tenants'

urlpatterns = [
    path('setup/', views.school_setup_wizard, name='setup_wizard'),
    path('landlord/', views.landlord_dashboard, name='landlord_dashboard'),
    path('approval-queue/', views.approval_queue, name='approval_queue'),
    path('review/<int:school_id>/', views.review_school, name='review_school'),
]
