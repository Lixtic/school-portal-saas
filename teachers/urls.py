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
    path('edit/<int:teacher_id>/', views.edit_teacher, name='edit_teacher'),
    path('assign-class/<int:class_id>/', views.assign_class_teacher, name='assign_class_teacher'),
    path('my-classes/', views.teacher_classes, name='my_classes'),
    path('schedule/', views.teacher_schedule, name='schedule'),
    path('grades/enter/', views.enter_grades, name='enter_grades'),
    path('get-students/<int:class_id>/', views.get_students, name='get_students'),
    path('duty-roster/', views.print_duty_roster, name='duty_roster'),
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
    path('lesson-plans/create/', views.lesson_plan_create, name='lesson_plan_create'),
    path('lesson-plans/aura-t-api/', views.aura_t_api, name='aura_t_api'),
    path('lesson-plans/aura-t-api/', views.aura_t_api, name='aura_t_api'),
    path('lesson-plans/<int:pk>/', views.lesson_plan_detail, name='lesson_plan_detail'),
    path('lesson-plans/<int:pk>/duplicate/', views.lesson_plan_duplicate, name='lesson_plan_duplicate'),
    path('lesson-plans/<int:pk>/print/', views.lesson_plan_print, name='lesson_plan_print'),
    path('lesson-plans/<int:pk>/edit/', views.lesson_plan_edit, name='lesson_plan_edit'),
    path('lesson-plans/<int:pk>/delete/', views.lesson_plan_delete, name='lesson_plan_delete'),
    
    # AI Chat Sessions
    path('ai-sessions/', views.ai_sessions_list, name='ai_sessions_list'),
    path('ai-sessions/new/', views.ai_session_new, name='ai_session_new'),
    path('ai-sessions/<int:session_id>/', views.ai_session_detail, name='ai_session_detail'),
    path('ai-sessions/<int:session_id>/rename/', views.ai_session_rename, name='ai_session_rename'),
    path('ai-sessions/<int:session_id>/delete/', views.ai_session_delete, name='ai_session_delete'),

    path('id-card/<int:teacher_id>/png/', views.teacher_id_card, name='id_card_png'),
    path('id-card/<int:teacher_id>/pdf/', views.teacher_id_card_pdf, name='id_card_pdf'),
    path('id-cards/bulk-pdf/', views.bulk_teacher_id_cards_pdf, name='bulk_id_cards_pdf'),
]


