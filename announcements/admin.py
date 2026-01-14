from django.contrib import admin
from .models import Announcement, Notification

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'target_audience', 'is_active', 'created_by', 'created_at')
    list_filter = ('target_audience', 'is_active', 'created_at')
    search_fields = ('title', 'content')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'message', 'is_read', 'created_at', 'alert_type')
    list_filter = ('is_read', 'alert_type', 'created_at')
    search_fields = ('recipient__username', 'message')
