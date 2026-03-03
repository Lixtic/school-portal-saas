from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    path('', views.finance_dashboard, name='dashboard'),
    path('manage/', views.manage_fees, name='manage_fees'),
    path('create-structure/', views.create_fee_structure, name='create_fee_structure'),
    path('structure/<int:structure_id>/edit/', views.edit_fee_structure, name='edit_fee_structure'),
    path('category/<int:head_id>/edit/', views.edit_fee_head, name='edit_fee_head'),
    path('student/<int:student_id>/', views.student_fees, name='student_fees'),
    path('payment/add/<int:fee_id>/', views.record_payment, name='record_payment'),
    path('receipt/<int:payment_id>/', views.print_receipt, name='print_receipt'),
    path('send-reminders/', views.send_fee_reminders, name='send_fee_reminders'),
]
