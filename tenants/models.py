from django.db import models
from django_tenants.models import TenantMixin, DomainMixin
from django.contrib.auth import get_user_model

class School(TenantMixin):
    name = models.CharField(max_length=100)
    created_on = models.DateField(auto_now_add=True)
    
    # New Comprehensive Fields
    SCHOOL_TYPES = (
        ('primary', 'Primary School (Class 1-6)'),
        ('jhs', 'Junior High School (JHS 1-3)'),
        ('shs', 'Senior High School'),
        ('basic', 'Basic School (Kindergarten - JHS 3)'),
        ('other', 'Other / Tertiary'),
    )
    school_type = models.CharField(max_length=20, choices=SCHOOL_TYPES, default='basic')
    address = models.TextField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=50, default="Ghana")
    
    on_trial = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Onboarding & Approval Workflow
    APPROVAL_STATUS = (
        ('pending', 'Pending Review'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('requires_info', 'Requires More Information'),
    )
    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUS,
        default='pending',
        help_text="Current approval status of the school"
    )
    
    # Contact Person
    contact_person_name = models.CharField(max_length=100, blank=True)
    contact_person_email = models.EmailField(blank=True)
    contact_person_phone = models.CharField(max_length=20, blank=True)
    contact_person_title = models.CharField(max_length=100, blank=True, help_text="e.g., Principal, Headmaster, Administrator")
    
    # Verification Documents
    registration_certificate = models.FileField(
        upload_to='school_credentials/registration/',
        blank=True,
        null=True,
        help_text="School registration certificate or license"
    )
    tax_id_document = models.FileField(
        upload_to='school_credentials/tax/',
        blank=True,
        null=True,
        help_text="Tax identification document"
    )
    additional_documents = models.FileField(
        upload_to='school_credentials/additional/',
        blank=True,
        null=True,
        help_text="Any additional verification documents"
    )
    
    # Approval Tracking
    submitted_for_review_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_schools'
    )
    admin_notes = models.TextField(blank=True, help_text="Internal notes for admin review")
    rejection_reason = models.TextField(blank=True, help_text="Reason for rejection if applicable")
    
    # Default true, schema will be automatically created and synced when it is saved
    auto_create_schema = True

    def __str__(self):
        return self.name

class Domain(DomainMixin):
    pass
