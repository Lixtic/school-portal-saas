from django.urls import path
from . import views, views_ai

app_name = 'students'

urlpatterns = [
    path('add/', views.add_student, name='add_student'),
    path('edit/<int:student_id>/', views.edit_student, name='edit_student'),
    path('', views.student_list, name='student_list'),
    path('import-csv/', views.import_students_csv, name='import_csv'),
    path('attendance/mark/', views.mark_attendance, name='mark_attendance'),
    path('get-class-students/<int:class_id>/', views.get_class_students, name='get_class_students'),
    path('dashboard/', views.student_dashboard_view, name='student_dashboard'),
    path('schedule/', views.student_schedule, name='student_schedule'),
    path('report-card/bulk/', views.bulk_report_cards, name='bulk_report_cards'),
    path('report-card/<int:student_id>/', views.generate_report_card, name='report_card'),
    path('details/<int:student_id>/', views.student_details_ajax, name='student_details'),
    path('bulk-assign-class/', views.bulk_assign_class, name='bulk_assign_class'),
    path('export/', views.export_students, name='export_students'),
    path('id-card/<int:student_id>/png/', views.student_id_card, name='id_card_png'),
    path('id-card/<int:student_id>/pdf/', views.student_id_card_pdf, name='id_card_pdf'),
    path('id-cards/bulk-pdf/', views.bulk_student_id_cards_pdf, name='bulk_id_cards_pdf'),
    path('at-risk/', views.at_risk_students, name='at_risk_students'),
    
    # AI Voice Interface
    path('aura/voice/', views_ai.aura_voice_view, name='aura_voice'),
    path('aura/process-voice/', views_ai.process_voice_interaction, name='process_voice'),
    
    # Aura Arena
    path('aura/arena/', views_ai.aura_arena_view, name='aura_arena'),
    path('aura/arena/api/', views_ai.aura_arena_api, name='aura_arena_api'),
]