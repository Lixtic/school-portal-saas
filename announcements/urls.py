from django.urls import path
from . import views

app_name = 'announcements'

urlpatterns = [
    path('', views.announcement_list, name='list'),
    path('manage/', views.manage_announcements, name='manage'),
    path('notifications/read/<int:notification_id>/', views.mark_notification_read, name='mark_read'),
    path('notifications/read-all/', views.mark_all_notifications_read, name='mark_all_read'),
]
