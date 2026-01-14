from django.urls import path
from . import views

urlpatterns = [
    path('', views.homework_list, name='homework_list'),
    path('create/', views.homework_create, name='homework_create'),
    path('<int:pk>/', views.homework_detail, name='homework_detail'),
    path('<int:pk>/delete/', views.homework_delete, name='homework_delete'),
]
