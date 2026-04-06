from django.urls import path
from . import views, views_ai

app_name = 'students'

urlpatterns = [
    path('add/', views.add_student, name='add_student'),
    path('edit/<int:student_id>/', views.edit_student, name='edit_student'),
    path('', views.student_list, name='student_list'),
    path('import-csv/', views.import_students_csv, name='import_csv'),
    path('attendance/mark/', views.mark_attendance, name='mark_attendance'),
    path('attendance/qr/', views.qr_attendance_page, name='qr_attendance_page'),
    path('attendance/qr/generate/', views.qr_attendance_generate, name='qr_attendance_generate'),
    path('attendance/qr/scan/', views.qr_attendance_scan, name='qr_attendance_scan'),
    path('attendance/report/', views.attendance_report, name='attendance_report'),
    path('attendance/export/csv/', views.export_attendance_csv, name='export_attendance_csv'),
    path('attendance/export/pdf/', views.export_attendance_pdf, name='export_attendance_pdf'),
    path('get-class-students/<int:class_id>/', views.get_class_students, name='get_class_students'),
    path('dashboard/', views.student_dashboard_view, name='student_dashboard'),
    path('schedule/', views.student_schedule, name='student_schedule'),
    path('report-card/bulk/', views.bulk_report_cards, name='bulk_report_cards'),
    path('report-card/<int:student_id>/', views.generate_report_card, name='report_card'),
    path('report-card/<int:student_id>/pdf/', views.generate_report_card_pdf, name='report_card_pdf'),
    path('detail/<int:student_id>/', views.student_detail_page, name='student_detail_page'),
    path('details/<int:student_id>/', views.student_details_ajax, name='student_details'),
    path('bulk-assign-class/', views.bulk_assign_class, name='bulk_assign_class'),
    path('export/', views.export_students, name='export_students'),
    path('id-card/<int:student_id>/png/', views.student_id_card, name='id_card_png'),
    path('id-card/<int:student_id>/pdf/', views.student_id_card_pdf, name='id_card_pdf'),
    path('id-cards/bulk-pdf/', views.bulk_student_id_cards_pdf, name='bulk_id_cards_pdf'),
    path('at-risk/', views.at_risk_students, name='at_risk_students'),

    # Gradebook CSV import / export
    path('grades/export/', views.export_grades_csv, name='export_grades_csv'),
    path('grades/import/', views.import_grades_csv, name='import_grades_csv'),

    # Bulk report cards ZIP
    path('report-card/class/<int:class_id>/zip/', views.bulk_report_cards_zip, name='bulk_report_cards_zip'),

    # Student Promotion
    path('promote/', views.promote_students, name='promote_students'),
    path('exam-types/', views.manage_exam_types, name='manage_exam_types'),
    
    # AI Voice Interface
    path('padi/voice/', views_ai.padi_voice_view, name='padi_voice'),
    path('padi/realtime-session/', views_ai.create_realtime_session, name='create_realtime_session'),
    path('padi/voice/end-session/', views_ai.voice_end_session, name='voice_end_session'),
    path('padi/voice/board/', views_ai.voice_board_generate, name='voice_board_generate'),
    path('padi/voice/vision/', views_ai.voice_vision_analyze, name='voice_vision_analyze'),
    
    # SchoolPadi Arena
    path('padi/arena/', views_ai.padi_arena_view, name='padi_arena'),
    path('padi/arena/api/', views_ai.padi_arena_api, name='padi_arena_api'),

    # Power Word tracking
    path('padi/log-power-words/', views_ai.log_power_words, name='log_power_words'),

    # Voice XP Award
    path('padi/voice/award-xp/', views_ai.voice_award_xp, name='voice_award_xp'),

    # SchoolPadi Portfolio (student + teacher/parent view)
    path('padi/portfolio/', views.padi_portfolio, name='padi_portfolio'),

    # SchoolPadi Preferences (student self-service)
    path('padi/preferences/', views.update_padi_preferences, name='update_padi_preferences'),

    # Power Words history (student view)
    path('power-words/', views.student_power_words, name='power_words_history'),

    # XP Leaderboard API
    path('padi/leaderboard/', views.class_leaderboard_json, name='class_leaderboard_json'),

    # Class Analytics
    path('class-analytics/', views.class_analytics, name='class_analytics'),

    # XP Leaderboard full page
    path('padi/leaderboard-page/', views.xp_leaderboard, name='xp_leaderboard'),

    # Digital Pulse (student side)
    path('pulse/poll/', views.pulse_poll, name='pulse_poll'),
    path('pulse/<int:session_id>/submit/', views.pulse_submit, name='pulse_submit'),

    # Student Progress Analytics
    path('progress/', views.student_progress_dashboard, name='student_progress_dashboard'),
]