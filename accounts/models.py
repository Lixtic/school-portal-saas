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