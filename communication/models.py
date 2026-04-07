from django.db import models
from django.conf import settings
from django.db.models import Q
from accounts.models import User


# ──────────────────────────────────────────────
# INTERNAL MESSAGING (Direct Messages / Threads)
# ──────────────────────────────────────────────

class Conversation(models.Model):
    """A thread between exactly two users. Participant order is normalised by pk."""
    participant1 = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='conversations_as_p1'
    )
    participant2 = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='conversations_as_p2'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['participant1', 'participant2']
        ordering = ['-updated_at']

    def __str__(self):
        return f"Thread: {self.participant1} ↔ {self.participant2}"

    @classmethod
    def get_or_create_between(cls, user_a, user_b):
        """Normalise order so the same pair always maps to one row."""
        p1, p2 = (user_a, user_b) if user_a.id < user_b.id else (user_b, user_a)
        return cls.objects.get_or_create(participant1=p1, participant2=p2)

    @classmethod
    def for_user(cls, user):
        """Return all conversations this user participates in."""
        return cls.objects.filter(
            Q(participant1=user) | Q(participant2=user)
        ).select_related('participant1', 'participant2').order_by('-updated_at')

    def other_participant(self, user):
        return self.participant2 if self.participant1_id == user.id else self.participant1

    def unread_count_for(self, user):
        return self.messages.filter(is_read=False).exclude(sender=user).count()

    def last_message(self):
        return self.messages.order_by('-created_at').first()


class Message(models.Model):
    """A single message within a Conversation thread."""
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name='messages'
    )
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='sent_direct_messages'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}"


# ──────────────────────────────────────────────
# BROADCAST MESSAGING (SMS / Email Campaigns)
# ──────────────────────────────────────────────

class SMSMessage(models.Model):
    STATUS_CHOICES = (
        ('queued', 'Queued'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    )
    
    recipient_number = models.CharField(max_length=20)
    message_body = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='queued')
    provider_response = models.TextField(blank=True, null=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"SMS to {self.recipient_number} ({self.status})"

class EmailCampaign(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sent', 'Sent'),
    )
    
    subject = models.CharField(max_length=200)
    body = models.TextField() # HTML supported
    recipient_group = models.CharField(max_length=20, choices=(
        ('staff', 'All Staff'),
        ('parents', 'All Parents'),
        ('students', 'All Students'),
    ))
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    sent_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"Email: {self.subject}"


# ──────────────────────────────────────────────
# AUTO PARENT NOTIFICATION RULES
# ──────────────────────────────────────────────

class NotificationRule(models.Model):
    """
    Admin-configurable rule that auto-notifies parents when conditions are met.
    Evaluated on-demand via a management view or on attendance/grade save signals.
    """
    TRIGGER_CHOICES = (
        ('attendance_below', 'Attendance drops below %'),
        ('grade_below', 'Average grade drops below %'),
        ('fee_overdue', 'Fee unpaid after X days'),
        ('absent_streak', 'Consecutive absences reach X days'),
    )
    CHANNEL_CHOICES = (
        ('in_app', 'In-App Notification'),
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('all', 'All Channels'),
    )

    name = models.CharField(max_length=200)
    trigger = models.CharField(max_length=30, choices=TRIGGER_CHOICES)
    threshold = models.DecimalField(
        max_digits=6, decimal_places=2,
        help_text='Percentage for attendance/grade, or number of days for fee_overdue/absent_streak',
    )
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES, default='in_app')
    is_active = models.BooleanField(default=True)
    cooldown_hours = models.PositiveIntegerField(
        default=24,
        help_text='Minimum hours between repeated alerts for the same student & rule',
    )
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_active', '-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_trigger_display()})"


class NotificationRuleLog(models.Model):
    """Records each time a rule fires for a student so we can enforce cooldown."""
    rule = models.ForeignKey(NotificationRule, on_delete=models.CASCADE, related_name='logs')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    parent = models.ForeignKey(User, on_delete=models.CASCADE)
    channel = models.CharField(max_length=10)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['rule', 'student', 'sent_at'], name='nrl_rule_student_sent_idx'),
        ]

    def __str__(self):
        return f"Log: {self.rule.name} → {self.student} @ {self.sent_at}"
