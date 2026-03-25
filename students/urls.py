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
    path('aura/voice/', views_ai.aura_voice_view, name='aura_voice'),
    path('aura/realtime-session/', views_ai.create_realtime_session, name='create_realtime_session'),
    path('aura/voice/end-session/', views_ai.voice_end_session, name='voice_end_session'),
    path('aura/voice/board/', views_ai.voice_board_generate, name='voice_board_generate'),
    path('aura/voice/vision/', views_ai.voice_vision_analyze, name='voice_vision_analyze'),
    
    # Aura Arena
    path('aura/arena/', views_ai.aura_arena_view, name='aura_arena'),
    path('aura/arena/api/', views_ai.aura_arena_api, name='aura_arena_api'),

    # Power Word tracking
    path('aura/log-power-words/', views_ai.log_power_words, name='log_power_words'),

    # Voice XP Award
    path('aura/voice/award-xp/', views_ai.voice_award_xp, name='voice_award_xp'),

    # Aura Portfolio (student + teacher/parent view)
    path('aura/portfolio/', views.aura_portfolio, name='aura_portfolio'),

    # Aura Preferences (student self-service)
    path('aura/preferences/', views.update_aura_preferences, name='update_aura_preferences'),

    # Power Words history (student view)
    path('power-words/', views.student_power_words, name='power_words_history'),

    # XP Leaderboard API
    path('aura/leaderboard/', views.class_leaderboard_json, name='class_leaderboard_json'),

    # Class Analytics
    path('class-analytics/', views.class_analytics, name='class_analytics'),

    # XP Leaderboard full page
    path('aura/leaderboard-page/', views.xp_leaderboard, name='xp_leaderboard'),

    # Digital Pulse (student side)
    path('pulse/poll/', views.pulse_poll, name='pulse_poll'),
    path('pulse/<int:session_id>/submit/', views.pulse_submit, name='pulse_submit'),
]