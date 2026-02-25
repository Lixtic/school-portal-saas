from django.urls import path
from . import views

app_name = 'communication'

urlpatterns = [
    # Inbox / Direct Messages
    path('', views.inbox, name='inbox'),
    path('inbox/', views.inbox, name='inbox_alt'),
    path('compose/', views.compose, name='compose'),
    path('thread/<int:user_id>/', views.conversation_view, name='conversation'),

    # API
    path('api/unread/', views.api_unread_count, name='api_unread'),

    # Admin Broadcasts
    path('broadcast/', views.broadcast_dashboard, name='broadcast_dashboard'),
    path('sms/send/', views.send_sms, name='send_sms'),
    path('email/send/', views.send_email, name='send_email'),
]
