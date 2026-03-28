# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    USER_TYPES = (
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
        ('parent', 'Parent'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPES)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"


class UserSettings(models.Model):
    """Per-user application preferences — stored per tenant schema."""
    user = models.OneToOneField(
        'User',
        on_delete=models.CASCADE,
        related_name='settings',
    )
    # Notification toggles
    notify_announcements = models.BooleanField(default=True)
    notify_grades        = models.BooleanField(default=True)
    notify_attendance    = models.BooleanField(default=True)
    notify_messages      = models.BooleanField(default=True)
    email_notifications  = models.BooleanField(default=False)

    # UI preferences
    compact_view = models.BooleanField(default=False)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Settings'
        verbose_name_plural = 'User Settings'

    def __str__(self):
        return f"Settings({self.user.username})"


class OnboardingProgress(models.Model):
    """Tracks per-user onboarding checklist progress."""
    user = models.OneToOneField(
        'User',
        on_delete=models.CASCADE,
        related_name='onboarding',
    )
    steps_completed = models.JSONField(default=list)
    dismissed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Onboarding({self.user.username})"

    def mark_step(self, step_id):
        if step_id not in self.steps_completed:
            self.steps_completed.append(step_id)
            return True
        return False