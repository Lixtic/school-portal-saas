from django.urls import path
from . import views

app_name = 'parents'

urlpatterns = [
    path('add/', views.add_parent, name='add_parent'),
    path('<int:parent_id>/edit/', views.edit_parent, name='edit_parent'),
    path('<int:parent_id>/delete/', views.delete_parent, name='delete_parent'),
    path('children/', views.parent_children, name='my_children'),
    path('children/<int:student_id>/', views.child_details, name='child_details'),
    path('children/<int:student_id>/fees/', views.child_fees, name='child_fees'),
    path('payments/', views.payment_history, name='payment_history'),
    path('send-message/', views.send_message_to_school, name='send_message'),
    path('teachers/', views.contact_teachers, name='contact_teachers'),
]