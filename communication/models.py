from django.db import models
from django.conf import settings
from accounts.models import User

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
