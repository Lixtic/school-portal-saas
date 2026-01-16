"""
System health monitoring and support desk models
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone


class SystemHealthMetric(models.Model):
    """Real-time system health metrics"""
    METRIC_TYPES = [
        ('cpu', 'CPU Usage'),
        ('memory', 'Memory Usage'),
        ('disk', 'Disk Usage'),
        ('db_latency', 'Database Latency'),
        ('api_uptime', 'API Uptime'),
        ('active_users', 'Active Users'),
    ]
    
    STATUS_CHOICES = [
        ('healthy', 'Healthy'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ]
    
    metric_type = models.CharField(max_length=20, choices=METRIC_TYPES)
    value = models.FloatField(help_text="Metric value (percentage, ms, count, etc.)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='healthy')
    details = models.JSONField(default=dict, blank=True)
    recorded_at = models.DateTimeField(default=timezone.now, db_index=True)
    
    class Meta:
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['metric_type', '-recorded_at']),
        ]
    
    def __str__(self):
        return f"{self.get_metric_type_display()}: {self.value} ({self.status})"


class SupportTicket(models.Model):
    """Support tickets from school administrators"""
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('waiting_response', 'Waiting for Response'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    CATEGORY_CHOICES = [
        ('technical', 'Technical Issue'),
        ('billing', 'Billing/Subscription'),
        ('feature', 'Feature Request'),
        ('bug', 'Bug Report'),
        ('account', 'Account Management'),
        ('other', 'Other'),
    ]
    
    ticket_number = models.CharField(max_length=20, unique=True, editable=False)
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='support_tickets')
    created_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, related_name='created_tickets')
    
    subject = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='technical')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    assigned_to = models.ForeignKey(
        get_user_model(), 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_tickets'
    )
    
    # Attachments
    attachment = models.FileField(upload_to='support_tickets/', blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['school', '-created_at']),
        ]
    
    def __str__(self):
        return f"#{self.ticket_number} - {self.subject}"
    
    def save(self, *args, **kwargs):
        if not self.ticket_number:
            # Generate ticket number: TKT-YYYYMMDD-XXXX
            from django.db.models import Max
            today = timezone.now().strftime('%Y%m%d')
            last_ticket = SupportTicket.objects.filter(
                ticket_number__startswith=f'TKT-{today}'
            ).aggregate(Max('id'))
            
            next_num = (last_ticket['id__max'] or 0) + 1
            self.ticket_number = f'TKT-{today}-{next_num:04d}'
        
        # Auto-set resolved/closed timestamps
        if self.status == 'resolved' and not self.resolved_at:
            self.resolved_at = timezone.now()
        if self.status == 'closed' and not self.closed_at:
            self.closed_at = timezone.now()
        
        super().save(*args, **kwargs)


class TicketComment(models.Model):
    """Comments/replies on support tickets"""
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True)
    message = models.TextField()
    is_staff_reply = models.BooleanField(default=False)
    is_internal = models.BooleanField(default=False, help_text="Internal note not visible to school")
    
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment on {self.ticket.ticket_number} by {self.user}"


class DatabaseBackup(models.Model):
    """Database backup records"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    BACKUP_TYPES = [
        ('full', 'Full Backup'),
        ('incremental', 'Incremental'),
        ('schema_only', 'Schema Only'),
    ]
    
    school = models.ForeignKey(
        'tenants.School', 
        on_delete=models.CASCADE, 
        related_name='backups',
        null=True,
        blank=True,
        help_text="Leave blank for system-wide backup"
    )
    
    backup_type = models.CharField(max_length=20, choices=BACKUP_TYPES, default='full')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Storage
    backup_file = models.CharField(max_length=500, blank=True, help_text="Cloud storage path")
    file_size_mb = models.FloatField(default=0)
    
    # Metadata
    is_encrypted = models.BooleanField(default=True)
    retention_days = models.IntegerField(default=30)
    
    # Timestamps
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['school', '-started_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        school_name = self.school.name if self.school else "System-wide"
        return f"{school_name} - {self.get_backup_type_display()} ({self.status})"
    
    def save(self, *args, **kwargs):
        # Calculate expiration date
        if not self.expires_at and self.retention_days:
            self.expires_at = self.started_at + timezone.timedelta(days=self.retention_days)
        
        super().save(*args, **kwargs)
