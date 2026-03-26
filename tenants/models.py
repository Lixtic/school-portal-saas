from django.db import models
from django_tenants.models import TenantMixin, DomainMixin
from django.contrib.auth import get_user_model

class School(TenantMixin):
    name = models.CharField(max_length=100)
    created_on = models.DateField(auto_now_add=True)
    
    # New Comprehensive Fields
    SCHOOL_TYPES = (
        ('primary', 'Primary School (KG 1 – B6)'),
        ('jhs', 'Junior High School (JHS 1-3)'),
        ('shs', 'Senior High School (SHS 1-3)'),
        ('basic', 'Basic School (KG 1 – JHS 3)'),
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


class PlatformSettings(models.Model):
    """Singleton model for platform-wide settings (public schema only)."""

    TEMPLATE_CHOICES = [
        ('home/classic.html',  'Classic — Sidebar Navigation'),
        ('home/modern.html',   'Modern — Bold Hero'),
        ('home/minimal.html',  'Minimal — Clean Cards'),
        ('home/playful.html',  'Playful — Colourful & Animated'),
        ('home/elegant.html',  'Elegant — Navy / Gold'),
        ('home/swiss.html',    'Swiss — Grid System'),
        ('home/glass.html',   'Glass — Digital Lucidity'),
        ('home/artdeco.html', 'Art Deco — Gilded Authority'),
        ('home/japandi.html', 'Japandi — Natural Clarity'),
    ]

    landing_template = models.CharField(
        max_length=60,
        choices=TEMPLATE_CHOICES,
        default='home/swiss.html',
        help_text="Which landing page template to show at /",
    )
    AI_PROVIDER_CHOICES = [
        ('openai', 'OpenAI'),
        ('gemini', 'Google Gemini'),
    ]

    ai_primary_provider = models.CharField(
        max_length=20,
        choices=AI_PROVIDER_CHOICES,
        default='openai',
        help_text="Default provider used across AI features unless a category model overrides provider.",
    )
    ai_model_general = models.CharField(
        max_length=80,
        default='openai:gpt-5-mini',
        help_text="General AI model for global assistant-style tasks.",
    )
    ai_model_admissions = models.CharField(
        max_length=80,
        default='openai:gpt-4o-mini',
        help_text="Admissions and public FAQ assistant model.",
    )
    ai_model_tutor = models.CharField(
        max_length=80,
        default='openai:gpt-5-nano',
        help_text="Tutor/copilot classroom workflows model.",
    )
    ai_model_analytics = models.CharField(
        max_length=80,
        default='openai:gpt-5-mini',
        help_text="Reports, summaries, and analytics-oriented model.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Platform Settings"
        verbose_name_plural = "Platform Settings"

    def save(self, *args, **kwargs):
        # Enforce singleton — always update row pk=1
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # never delete the singleton

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return f"Platform Settings (template: {self.landing_template})"

    @staticmethod
    def parse_model_ref(model_ref, fallback_provider='openai'):
        raw = str(model_ref or '').strip()
        provider = str(fallback_provider or 'openai').strip().lower()
        model = raw

        if ':' in raw:
            pfx, rest = raw.split(':', 1)
            pfx = pfx.strip().lower()
            if pfx in {'openai', 'gemini'} and rest.strip():
                provider = pfx
                model = rest.strip()
        elif raw.startswith('gemini'):
            provider = 'gemini'
        elif raw.startswith('gpt-') or raw.startswith('o'):
            provider = 'openai'

        return provider, model

    def get_ai_category_config(self, category='general'):
        field_name = f'ai_model_{category}'
        model_ref = getattr(self, field_name, '') if hasattr(self, field_name) else ''
        provider, model = self.parse_model_ref(model_ref, fallback_provider=self.ai_primary_provider)
        return {
            'category': category,
            'provider': provider,
            'model': model,
            'model_ref': f'{provider}:{model}' if model else '',
        }


# Import subscription models
from .subscription_models import (
    SubscriptionPlan, AddOn, SchoolSubscription,
    SchoolAddOn, Invoice, ChurnEvent, AIUsageLog,
)

from .health_models import (
    SystemHealthMetric, SupportTicket, TicketComment, DatabaseBackup
)
