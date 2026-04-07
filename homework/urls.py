from django.urls import path
from . import views

app_name = 'homework'

urlpatterns = [
    path('', views.homework_list, name='homework_list'),
    path('notes/', views.student_notes_list, name='student_notes_list'),
    path('create/', views.homework_create, name='homework_create'),
    path('ai-generate/', views.homework_ai_generate, name='homework_ai_generate'),
    path('<int:pk>/', views.homework_detail, name='homework_detail'),
    path('<int:pk>/edit/', views.homework_edit, name='homework_edit'),
    path('<int:pk>/delete/', views.homework_delete, name='homework_delete'),
    path('<int:pk>/questions/', views.homework_add_questions, name='homework_add_questions'),
    path('<int:pk>/solve/', views.homework_solve, name='homework_solve'),
    path('<int:pk>/results/', views.homework_results, name='homework_results'),
    path('<int:pk>/class-results/', views.homework_class_results, name='homework_class_results'),
    path('<int:pk>/push-grades/', views.homework_push_grades, name='homework_push_grades'),
    path('<int:pk>/export-csv/', views.homework_export_csv, name='homework_export_csv'),

    # Deadline Reminders
    path('deadline-reminders/', views.deadline_reminders, name='deadline_reminders'),
    path('deadline-reminders/save/', views.reminder_setting_save, name='reminder_setting_save'),
    path('deadline-reminders/<int:pk>/delete/', views.reminder_setting_delete, name='reminder_setting_delete'),
    path('deadline-reminders/<int:pk>/toggle/', views.reminder_setting_toggle, name='reminder_setting_toggle'),
    path('deadline-reminders/evaluate/', views.evaluate_deadline_reminders, name='evaluate_deadline_reminders'),
]
