from django.urls import path
from . import views

app_name = 'announcements'

urlpatterns = [
    path('', views.announcement_list, name='list'),
    path('manage/', views.manage_announcements, name='manage'),
    path('notifications/', views.notification_centre, name='notification_centre'),
    path('notifications/read/<int:notification_id>/', views.mark_notification_read, name='mark_read'),
    path('notifications/read-all/', views.mark_all_notifications_read, name='mark_all_read'),
    path('notifications/unread-count/', views.notifications_unread_count, name='notifications_unread_count'),
    # Push subscription endpoints
    path('push/subscribe/', views.push_subscribe, name='push_subscribe'),
    path('push/unsubscribe/', views.push_unsubscribe, name='push_unsubscribe'),

    # Offline Data API
    path('api/offline/', views.offline_announcements_json, name='offline_announcements'),
]
