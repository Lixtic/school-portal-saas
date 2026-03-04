from django.db import models
from accounts.models import User

class Announcement(models.Model):
    TARGET_CHOICES = (
        ('all', 'All Users'),
        ('staff', 'Staff Only (Admin & Teachers)'),
        ('teachers', 'Teachers Only'),
        ('students', 'Students Only'),
        ('parents', 'Parents Only'),
    )
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    target_audience = models.CharField(max_length=20, choices=TARGET_CHOICES, default='all')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return self.title


class Notification(models.Model):
    ALERT_CHOICES = [
        ('45_min', '45 Minutes Before Class'),
        ('10_min', '10 Minutes Before Class'),
        ('announcement', 'Announcement'),
        ('message', 'New Message'),
        ('general', 'General'),
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.CharField(max_length=500, blank=True, default='')

    # Optional links to source objects
    timetable_slot = models.ForeignKey('academics.Timetable', on_delete=models.CASCADE, null=True, blank=True)
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    alert_type = models.CharField(max_length=20, choices=ALERT_CHOICES, default='general')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.recipient}: {self.message}"


class PushSubscription(models.Model):
    """WebPush subscription endpoint + keys for a given user/device."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='push_subscriptions')
    endpoint = models.TextField(unique=True)
    p256dh = models.TextField()
    auth = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"PushSubscription({self.user}, {self.endpoint[:40]}...)"
