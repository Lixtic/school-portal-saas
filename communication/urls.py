from django.urls import path
from . import views

app_name = 'communication'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('sms/send/', views.send_sms, name='send_sms'),
    path('email/send/', views.send_email, name='send_email'),
]
