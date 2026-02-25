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
