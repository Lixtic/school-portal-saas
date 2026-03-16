from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    path('', views.finance_dashboard, name='dashboard'),
    path('manage/', views.manage_fees, name='manage_fees'),
    path('create-structure/', views.create_fee_structure, name='create_fee_structure'),
    path('structure/<int:structure_id>/edit/', views.edit_fee_structure, name='edit_fee_structure'),
    path('structure/<int:structure_id>/collected/', views.fee_collected_students, name='fee_collected_students'),
    path('structure/<int:structure_id>/assign-collector/', views.assign_fee_collector, name='assign_fee_collector'),
    path('category/<int:head_id>/edit/', views.edit_fee_head, name='edit_fee_head'),
    path('student/<int:student_id>/', views.student_fees, name='student_fees'),
    path('payment/add/<int:fee_id>/', views.record_payment, name='record_payment'),
    path('receipt/<int:payment_id>/', views.print_receipt, name='print_receipt'),
    path('send-reminders/', views.send_fee_reminders, name='send_fee_reminders'),
    path('bulk-assign/', views.bulk_assign_fees, name='bulk_assign_fees'),
    path('receipt/<int:payment_id>/pdf/', views.payment_receipt_pdf, name='receipt_pdf'),
    # Paystack online payment
    path('paystack/pay/<int:fee_id>/', views.initiate_paystack_payment, name='paystack_pay'),
    path('paystack/callback/', views.paystack_callback, name='paystack_callback'),
    path('paystack/webhook/', views.paystack_webhook, name='paystack_webhook'),
    # SMS fee reminders
    path('sms-reminders/', views.send_sms_fee_reminders, name='sms_fee_reminders'),
]
