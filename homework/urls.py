from django.urls import path
from . import views

app_name = 'homework'

urlpatterns = [
    path('', views.homework_list, name='homework_list'),
    path('create/', views.homework_create, name='homework_create'),
    path('<int:pk>/', views.homework_detail, name='homework_detail'),
    path('<int:pk>/delete/', views.homework_delete, name='homework_delete'),
    path('<int:pk>/questions/', views.homework_add_questions, name='homework_add_questions'),
    path('<int:pk>/solve/', views.homework_solve, name='homework_solve'),
    path('<int:pk>/results/', views.homework_results, name='homework_results'),
    path('<int:pk>/class-results/', views.homework_class_results, name='homework_class_results'),
]
