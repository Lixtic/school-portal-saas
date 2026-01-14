from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('add/', views.add_student, name='add_student'),
    path('edit/<int:student_id>/', views.edit_student, name='edit_student'),
    path('', views.student_list, name='student_list'),
    path('attendance/mark/', views.mark_attendance, name='mark_attendance'),
    path('get-class-students/<int:class_id>/', views.get_class_students, name='get_class_students'),
    path('dashboard/', views.student_dashboard_view, name='student_dashboard'),
    path('schedule/', views.student_schedule, name='student_schedule'),
    path('report-card/bulk/', views.bulk_report_cards, name='bulk_report_cards'),
    path('report-card/<int:student_id>/', views.generate_report_card, name='report_card'),
    path('details/<int:student_id>/', views.student_details_ajax, name='student_details'),
    path('bulk-assign-class/', views.bulk_assign_class, name='bulk_assign_class'),
    path('export/', views.export_students, name='export_students'),
]