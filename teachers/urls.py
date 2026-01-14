from django.urls import path
from . import views

app_name = 'teachers'

urlpatterns = [
    path('add/', views.add_teacher, name='add_teacher'),
    path('edit/<int:teacher_id>/', views.edit_teacher, name='edit_teacher'),
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
    path('lesson-plans/<int:pk>/', views.lesson_plan_detail, name='lesson_plan_detail'),
    path('lesson-plans/<int:pk>/edit/', views.lesson_plan_edit, name='lesson_plan_edit'),
    path('lesson-plans/<int:pk>/delete/', views.lesson_plan_delete, name='lesson_plan_delete'),
]