from django.urls import path
from . import views

app_name = 'curriculum'

urlpatterns = [
    path('api/subjects/', views.curriculum_subjects, name='subjects'),
    path('api/grades/', views.curriculum_grades, name='grades'),
    path('api/strands/', views.curriculum_strands, name='strands'),
    path('api/indicators/', views.curriculum_indicators, name='indicators'),
    path('api/pacing/', views.curriculum_pacing, name='pacing'),
]
