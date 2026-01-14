from django.urls import path
from . import views

app_name = 'business'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/add/', views.add_expense, name='add_expense'),
    path('assets/', views.asset_list, name='asset_list'),
]
