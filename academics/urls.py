from django.urls import path
from . import views

app_name = 'academics'

urlpatterns = [
    path('copilot/', views.copilot_assistant, name='copilot_assistant'),
    path('copilot/history/', views.copilot_history, name='copilot_history'),
    path('admissions/assistant/', views.admissions_assistant, name='admissions_assistant'),
    path('help/', views.help_page, name='help_page'),
    path('help/chat/', views.help_chat_api, name='help_chat'),
    path('activities/', views.activities_public, name='activities'),
    path('activities/manage/', views.manage_activities, name='manage_activities'),
    
    # Class Management
    path('classes/manage/', views.manage_classes, name='manage_classes'),
    path('classes/add/', views.add_class, name='add_class'),
    path('classes/bulk-add/', views.bulk_add_classes, name='bulk_add_classes'),
    path('classes/<int:class_id>/edit/', views.edit_class, name='edit_class'),
    path('classes/<int:class_id>/delete/', views.delete_class, name='delete_class'),
    path('classes/<int:class_id>/subjects/', views.manage_class_subjects, name='manage_class_subjects'),
    
    # Subject Management
    path('subjects/manage/', views.manage_subjects, name='manage_subjects'),
    path('subjects/add/', views.add_subject, name='add_subject'),
    path('subjects/bulk-add/', views.bulk_add_subjects, name='bulk_add_subjects'),
    path('subjects/<int:subject_id>/edit/', views.edit_subject, name='edit_subject'),
    path('subjects/<int:subject_id>/delete/', views.delete_subject, name='delete_subject'),
    
    # Academic Year Management
    path('years/manage/', views.manage_academic_years, name='manage_academic_years'),
    path('years/add/', views.add_academic_year, name='add_academic_year'),
    path('years/<int:year_id>/edit/', views.edit_academic_year, name='edit_academic_year'),
    path('years/<int:year_id>/delete/', views.delete_academic_year, name='delete_academic_year'),
    path('years/<int:year_id>/set-current/', views.set_current_year, name='set_current_year'),
    
    # ID Card Management
    path('id-cards/', views.manage_id_cards, name='manage_id_cards'),

    path('gallery/', views.gallery_view, name='gallery'),
    path('gallery/upload/', views.upload_gallery_image, name='upload_gallery_image'),
    path('resources/manage/', views.manage_resources, name='manage_resources'),
    path('resources/delete/<int:resource_id>/', views.delete_resource, name='delete_resource'),
    path('settings/', views.school_settings_view, name='school_settings'),
    path('settings/grading-scale/', views.grading_scale_view, name='grading_scale'),
    path('settings/preview/', views.preview_homepage, name='preview_homepage'),
    path('exams/', views.exam_schedule_list, name='exam_schedule'),
    path('exams/create/', views.exam_schedule_create, name='exam_schedule_create'),
    path('exams/<int:pk>/edit/', views.exam_schedule_edit, name='exam_schedule_edit'),
    path('exams/<int:pk>/delete/', views.exam_schedule_delete, name='exam_schedule_delete'),
    path('timetable/', views.timetable_view, name='timetable'),
    path('timetable/edit/<int:class_id>/', views.edit_timetable, name='edit_timetable'),
    path('timetable/conflicts/', views.timetable_conflicts, name='timetable_conflicts'),
    path('global-search/', views.global_search, name='global_search'),
    path('about/', views.about_us, name='about_us'),
    path('system-about/', views.system_about, name='system_about'),
    path('apply/', views.apply_admission, name='apply_admission'),
    path('admissions/', views.admission_applications, name='admission_applications'),
    path('admissions/<int:pk>/', views.admission_application_detail, name='admission_application_detail'),
    
    # AI Tutor
    path('ai-tutor/', views.ai_tutor, name='ai_tutor'),
    path('ai-tutor/chat/', views.ai_tutor_chat, name='ai_tutor_chat'),
    path('ai-tutor/generate-image/', views.generate_tutor_image, name='generate_tutor_image'),
    path('ai-tutor/session/new/', views.ai_tutor_new_session, name='ai_tutor_new_session'),
    path('ai-tutor/practice/', views.generate_practice, name='generate_practice'),
    path('ai-tutor/scheme-topic/', views.scheme_topic_suggest, name='scheme_topic_suggest'),
    path('ai-tutor/practice/<int:practice_set_id>/assign-homework/', views.assign_practice_as_homework, name='assign_practice_as_homework'),
    path('ai-tutor/explain/', views.explain_concept, name='explain_concept'),
    path('ai-tutor/sessions/', views.tutor_sessions, name='tutor_sessions'),

    # Shared State Manager (cross-session: text ↔ voice)
    path('aura/state/', views.aura_session_state, name='aura_session_state'),
    # Session rename (inline edit in sidebar)
    path('ai-tutor/sessions/<int:session_id>/rename/', views.rename_tutor_session, name='rename_session'),
    # Session delete (single and bulk)
    path('ai-tutor/sessions/<int:session_id>/delete/', views.delete_tutor_session, name='delete_session'),
    path('ai-tutor/sessions/delete-all/', views.delete_all_tutor_sessions, name='delete_all_sessions'),

    # Offline Data API
    path('api/offline/timetable/', views.offline_timetable_json, name='offline_timetable'),
]
