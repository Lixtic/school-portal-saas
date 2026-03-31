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
    path('lesson-plans/indicators-api/', views.scheme_of_work_indicators_api, name='scheme_of_work_indicators_api'),
    path('lesson-plans/aura-t-api/', views.aura_t_api, name='aura_t_api'),
    path('lesson-plans/ges-api/', views.ges_lesson_api, name='ges_lesson_api'),
    path('lesson-plans/save-aura-t/', views.save_aura_t_plan, name='save_aura_t_plan'),
    path('lesson-plans/<int:pk>/', views.lesson_plan_detail, name='lesson_plan_detail'),
    path('lesson-plans/<int:pk>/duplicate/', views.lesson_plan_duplicate, name='lesson_plan_duplicate'),
    path('lesson-plans/<int:pk>/print/', views.lesson_plan_print, name='lesson_plan_print'),
    path('lesson-plans/<int:pk>/pdf/', views.lesson_plan_pdf, name='lesson_plan_pdf'),
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
    path('scheme-of-work/<int:pk>/edit/', views.scheme_of_work_edit, name='scheme_of_work_edit'),
    path('scheme-of-work/<int:pk>/dedup/', views.scheme_of_work_dedup_indicators, name='scheme_of_work_dedup_indicators'),

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
    path('presentations/api/generate-image/', views.generate_slide_image, name='presentation_generate_image'),
    path('presentations/share/<uuid:token>/', views.presentation_share, name='presentation_share'),
    path('presentations/<int:pk>/edit/', views.presentation_editor, name='presentation_editor'),
    path('presentations/<int:pk>/present/', views.presentation_present, name='presentation_present'),
    path('presentations/<int:pk>/duplicate/', views.presentation_duplicate, name='presentation_duplicate'),
    path('presentations/<int:pk>/print/', views.presentation_print, name='presentation_print'),
    path('presentations/<int:pk>/delete/', views.presentation_delete, name='presentation_delete'),
    path('presentations/<int:pk>/sessions/', views.presentation_session_report, name='presentation_session_report'),
    path('presentations/<int:pk>/study-guide/', views.presentation_study_guide, name='presentation_study_guide'),
    path('presentations/<int:pk>/pulse-launch/', views.presentation_pulse_launch, name='presentation_pulse_launch'),
    path('presentations/<int:pk>/send-assignment/', views.presentation_send_as_assignment, name='presentation_send_as_assignment'),
    path('presentations/<int:pk>/send-notes/', views.presentation_send_as_notes, name='presentation_send_as_notes'),
    path('presentations/<int:pk>/start-live/', views.start_live_session, name='start_live_session'),
    path('presentations/<int:pk>/end-live/', views.end_live_session, name='end_live_session'),
    path('presentations/<int:pk>/update-live/', views.update_live_slide, name='update_live_slide'),
    path('live/<str:code>/', views.live_student, name='live_student'),
    path('live/<str:code>/state/', views.live_state, name='live_state'),
    path('live/<str:code>/vote/', views.live_vote, name='live_vote'),
    path('live/<str:code>/results/<int:slide_pk>/', views.live_results, name='live_results'),
    path('live/<str:code>/time/', views.log_slide_time, name='log_slide_time'),
    path('presentations/<int:pk>/export-pptx/', views.presentation_export_pptx, name='presentation_export_pptx'),
    path('presentations/bulk-action/', views.presentation_bulk_action, name='presentation_bulk_action'),
    # Fee collection tasks
    path('fee-tasks/', views.my_fee_tasks, name='my_fee_tasks'),
    path('fee-tasks/<int:structure_id>/', views.fee_task_detail, name='fee_task_detail'),

    # Teacher Add-On Store
    path('store/', views.teacher_store, name='teacher_store'),
    path('store/purchase/<int:addon_id>/', views.teacher_store_purchase, name='teacher_store_purchase'),
    path('store/verify/', views.teacher_store_verify, name='teacher_store_verify'),
    path('store/cancel/<int:addon_id>/', views.teacher_store_cancel, name='teacher_store_cancel'),
    path('store/trial/<int:addon_id>/', views.teacher_store_trial, name='teacher_store_trial'),
    path('store/webhook/', views.paystack_teacher_webhook, name='paystack_teacher_webhook'),
    path('my-addons/', views.my_addons, name='my_addons'),

    # Add-On Feature Views
    path('addons/task-board/', views.addon_task_board, name='addon_task_board'),
    path('addons/cpd-tracker/', views.addon_cpd_tracker, name='addon_cpd_tracker'),
    path('addons/observation-notes/', views.addon_observation_notes, name='addon_observation_notes'),
    path('addons/rubric-designer/', views.addon_rubric_designer, name='addon_rubric_designer'),
    path('addons/study-guide/', views.addon_study_guide, name='addon_study_guide'),
    path('addons/study-guide/ai/', views.study_guide_ai, name='study_guide_ai'),
    path('addons/random-picker/', views.addon_random_picker, name='addon_random_picker'),
    path('addons/countdown-timer/', views.addon_countdown_timer, name='addon_countdown_timer'),
    path('addons/noise-meter/', views.addon_noise_meter, name='addon_noise_meter'),
    path('addons/stem-pack/', views.addon_stem_pack, name='addon_stem_pack'),
    path('addons/creative-arts/', views.addon_creative_arts, name='addon_creative_arts'),

    # Wave 2 Add-On Feature Views
    path('addons/report-card/', views.addon_report_card, name='addon_report_card'),
    path('addons/report-card/ai/', views.report_card_ai, name='report_card_ai'),
    path('addons/question-bank/', views.addon_question_bank, name='addon_question_bank'),
    path('addons/question-bank/ai/', views.question_bank_ai, name='question_bank_ai'),
    path('addons/question-bank/paper/', views.addon_exam_paper, name='addon_exam_paper'),
    path('addons/behavior/', views.addon_behavior_tracker, name='addon_behavior_tracker'),
    path('addons/differentiated/', views.addon_differentiated, name='addon_differentiated'),
    path('addons/differentiated/ai/', views.differentiated_ai, name='differentiated_ai'),
    path('addons/live-quiz/', views.addon_live_quiz, name='addon_live_quiz'),
    path('addons/live-quiz/<int:quiz_id>/run/', views.live_quiz_run, name='live_quiz_run'),
    path('addons/live-quiz/<int:quiz_id>/api/', views.live_quiz_api, name='live_quiz_api'),
    path('quiz/<str:code>/', views.live_quiz_play, name='live_quiz_play'),
    path('quiz/<str:code>/api/', views.live_quiz_student_api, name='live_quiz_student_api'),
]




