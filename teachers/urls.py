from django.urls import path
from . import views

app_name = 'teachers'

urlpatterns = [
    path('', views.teacher_list, name='teacher_list'),
    path('ai-insights/', views.teacher_ai_insights, name='teacher_ai_insights'),
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    path('analytics/boost/', views.boost_intervention, name='boost_intervention'),
    path('analytics/generate-lesson/', views.generate_remedial_lesson, name='generate_remedial_lesson'),
    path('<int:teacher_id>/', views.teacher_detail, name='teacher_detail'),
    path('add/', views.add_teacher, name='add_teacher'),
    path('import-csv/', views.import_teachers_csv, name='import_csv'),
    path('edit/<int:teacher_id>/', views.edit_teacher, name='edit_teacher'),
    path('assign-class/<int:class_id>/', views.assign_class_teacher, name='assign_class_teacher'),
    path('my-classes/', views.teacher_classes, name='my_classes'),
    path('schedule/', views.teacher_schedule, name='schedule'),
    path('grades/enter/', views.enter_grades, name='enter_grades'),
    path('grades/scan/', views.scan_grades_sheet, name='scan_grades_sheet'),
    path('get-students/<int:class_id>/', views.get_students, name='get_students'),
    path('duty-roster/', views.print_duty_roster, name='duty_roster'),
    path('duty-roster/generate/', views.generate_duty_weeks, name='generate_duty_weeks'),
    # Exercises
    path('exercises/<int:class_subject_id>/', views.manage_exercises, name='manage_exercises'),
    path('exercises/<int:exercise_id>/scores/', views.enter_exercise_scores, name='enter_exercise_scores'),
    # Search
    path('search/', views.search_students, name='search_students'),
    # Resources
    path('curriculum/library/', views.curriculum_library, name='curriculum_library'),
    path('resources/<int:class_subject_id>/', views.class_resources, name='class_resources'),
    path('resources/delete/<int:resource_id>/', views.delete_resource, name='delete_resource'),
    # Lesson Plans
    path('lesson-plans/', views.lesson_plan_list, name='lesson_plan_list'),
    path('lesson-plans/command-center/', views.aura_command_center, name='aura_command_center'),
    path('lesson-plans/flight-manual/', views.aura_flight_manual, name='aura_flight_manual'),
    path('lesson-plans/create/', views.lesson_plan_create, name='lesson_plan_create'),
    path('lesson-plans/aura-t-api/', views.aura_t_api, name='aura_t_api'),
    path('lesson-plans/save-aura-t/', views.save_aura_t_plan, name='save_aura_t_plan'),
    path('lesson-plans/<int:pk>/', views.lesson_plan_detail, name='lesson_plan_detail'),
    path('lesson-plans/<int:pk>/duplicate/', views.lesson_plan_duplicate, name='lesson_plan_duplicate'),
    path('lesson-plans/<int:pk>/print/', views.lesson_plan_print, name='lesson_plan_print'),
    path('lesson-plans/<int:pk>/cards/', views.lesson_plan_cards_print, name='lesson_plan_cards_print'),
    path('lesson-plans/<int:pk>/edit/', views.lesson_plan_edit, name='lesson_plan_edit'),
    path('lesson-plans/<int:pk>/delete/', views.lesson_plan_delete, name='lesson_plan_delete'),
    
    # AI Chat Sessions
    path('ai-sessions/', views.ai_sessions_list, name='ai_sessions_list'),
    path('ai-sessions/new/', views.ai_session_new, name='ai_session_new'),
    path('ai-sessions/<int:session_id>/', views.ai_session_detail, name='ai_session_detail'),
    path('ai-sessions/<int:session_id>/rename/', views.ai_session_rename, name='ai_session_rename'),
    path('ai-sessions/<int:session_id>/delete/', views.ai_session_delete, name='ai_session_delete'),
    
    # AI Assignment Creator
    path('ai-assignments/', views.assignment_creator, name='assignment_creator'),

    path('id-card/<int:teacher_id>/png/', views.teacher_id_card, name='id_card_png'),
    path('id-card/<int:teacher_id>/pdf/', views.teacher_id_card_pdf, name='id_card_pdf'),
    path('id-cards/bulk-pdf/', views.bulk_teacher_id_cards_pdf, name='bulk_id_cards_pdf'),

    # Power Words — Teacher Command Center
    path('power-words/', views.power_words_dashboard, name='power_words_dashboard'),
    path('power-words/action/', views.power_words_action, name='power_words_action'),

    # Scheme of Work
    path('scheme-of-work/', views.scheme_of_work_list, name='scheme_of_work_list'),
    path('scheme-of-work/upload/', views.scheme_of_work_upload, name='scheme_of_work_upload'),
    path('scheme-of-work/<int:pk>/delete/', views.scheme_of_work_delete, name='scheme_of_work_delete'),
    path('scheme-of-work/<int:pk>/topics/', views.scheme_of_work_update_topics, name='scheme_of_work_update_topics'),
    path('scheme-of-work/<int:pk>/re-extract/', views.scheme_of_work_reextract, name='scheme_of_work_reextract'),
    path('scheme-of-work/<int:pk>/bulk-generate/', views.scheme_of_work_bulk_generate, name='scheme_of_work_bulk_generate'),

    # Student session peek (read-only tutor transcript for teacher)
    path('student-session/<int:session_id>/', views.student_session_peek, name='student_session_peek'),

    # Submit to HoD
    path('submit-to-hod/', views.submit_to_hod, name='submit_to_hod'),

    # Digital Pulse
    path('pulse/history/', views.pulse_history, name='pulse_history'),
    path('pulse/launch/<int:plan_pk>/', views.pulse_launch, name='pulse_launch'),
    path('pulse/<int:session_id>/live/', views.pulse_live, name='pulse_live'),
    path('pulse/<int:session_id>/close/', views.pulse_close, name='pulse_close'),
    path('pulse/<int:session_id>/results/', views.pulse_results, name='pulse_results'),

    # Slide Deck Creator (Gamma-style)
    path('presentations/', views.presentation_list, name='presentation_list'),
    path('presentations/create/', views.presentation_create, name='presentation_create'),
    path('presentations/api/', views.presentation_api, name='presentation_api'),
    path('presentations/api/upload-doc/', views.presentation_generate_from_doc, name='presentation_generate_from_doc'),
    path('presentations/api/from-youtube/', views.presentation_from_youtube, name='presentation_from_youtube'),
    path('presentations/api/lesson-plans/', views.presentation_lesson_plans, name='presentation_lesson_plans'),
    path('presentations/api/upload-image/', views.presentation_slide_image_upload, name='presentation_slide_image_upload'),
    path('presentations/share/<uuid:token>/', views.presentation_share, name='presentation_share'),
    path('presentations/<int:pk>/edit/', views.presentation_editor, name='presentation_editor'),
    path('presentations/<int:pk>/present/', views.presentation_present, name='presentation_present'),
    path('presentations/<int:pk>/duplicate/', views.presentation_duplicate, name='presentation_duplicate'),
    path('presentations/<int:pk>/print/', views.presentation_print, name='presentation_print'),
    path('presentations/<int:pk>/delete/', views.presentation_delete, name='presentation_delete'),
    path('presentations/<int:pk>/sessions/', views.presentation_session_report, name='presentation_session_report'),
    path('presentations/<int:pk>/start-live/', views.start_live_session, name='start_live_session'),
    path('presentations/<int:pk>/end-live/', views.end_live_session, name='end_live_session'),
    path('presentations/<int:pk>/update-live/', views.update_live_slide, name='update_live_slide'),
    path('live/<str:code>/', views.live_student, name='live_student'),
    path('live/<str:code>/state/', views.live_state, name='live_state'),
    path('live/<str:code>/vote/', views.live_vote, name='live_vote'),
    path('live/<str:code>/results/<int:slide_pk>/', views.live_results, name='live_results'),
]




