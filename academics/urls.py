from django.urls import path
from . import views

app_name = 'academics'

urlpatterns = [
    path('copilot/', views.copilot_assistant, name='copilot_assistant'),
    path('admissions/assistant/', views.admissions_assistant, name='admissions_assistant'),
    path('activities/', views.activities_public, name='activities'),
    path('activities/manage/', views.manage_activities, name='manage_activities'),
    path('classes/manage/', views.manage_classes, name='manage_classes'),
    path('gallery/', views.gallery_view, name='gallery'),
    path('gallery/upload/', views.upload_gallery_image, name='upload_gallery_image'),
    path('resources/manage/', views.manage_resources, name='manage_resources'),
    path('resources/delete/<int:resource_id>/', views.delete_resource, name='delete_resource'),
    path('settings/', views.school_settings_view, name='school_settings'),
    path('settings/preview/', views.preview_homepage, name='preview_homepage'),
    path('timetable/', views.timetable_view, name='timetable'),
    path('timetable/edit/<int:class_id>/', views.edit_timetable, name='edit_timetable'),
    path('global-search/', views.global_search, name='global_search'),
    path('about/', views.about_us, name='about_us'),
    path('apply/', views.apply_admission, name='apply_admission'),
    
    # AI Tutor
    path('ai-tutor/', views.ai_tutor, name='ai_tutor'),
    path('ai-tutor/chat/', views.ai_tutor_chat, name='ai_tutor_chat'),
    path('ai-tutor/practice/', views.generate_practice, name='generate_practice'),
    path('ai-tutor/explain/', views.explain_concept, name='explain_concept'),
    path('ai-tutor/sessions/', views.tutor_sessions, name='tutor_sessions'),
]
