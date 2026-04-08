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


class PromoCampaign(models.Model):
    """Landlord promotional email / in-app campaign."""

    AUDIENCE_CHOICES = [
        ('all_schools', 'All Active Schools'),
        ('trial_schools', 'Trial Schools Only'),
        ('approved_schools', 'Approved Schools Only'),
        ('individual_teachers', 'Individual Portal Teachers'),
        ('individual_all', 'All Individual Portal Users'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sent', 'Sent'),
    ]
    TEMPLATE_CHOICES = [
        ('', 'Custom (write your own)'),
        ('feature_launch', 'Feature Launch'),
        ('back_to_school', 'Back to School'),
        ('discount_offer', 'Discount / Promo Offer'),
        ('re_engagement', 'Re-engagement'),
        ('newsletter', 'Newsletter Update'),
    ]

    title = models.CharField(max_length=200)
    subject = models.CharField(max_length=200, help_text='Email subject line')
    body_html = models.TextField(help_text='HTML email body')
    audience = models.CharField(max_length=30, choices=AUDIENCE_CHOICES, default='all_schools')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    template_key = models.CharField(
        max_length=30, blank=True, default='',
        choices=TEMPLATE_CHOICES,
        help_text='Pre-built email template style',
    )
    scheduled_for = models.DateTimeField(
        null=True, blank=True,
        help_text='Schedule send for a future date/time (UTC)',
    )
    sent_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        get_user_model(), on_delete=models.SET_NULL,
        null=True, blank=True, related_name='promo_campaigns',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Promo Campaign'

    def __str__(self):
        return f'{self.title} ({self.status})'

    @property
    def is_due(self):
        """Check if a scheduled campaign is past its send time."""
        if self.status == 'scheduled' and self.scheduled_for:
            from django.utils import timezone as _tz
            return _tz.now() >= self.scheduled_for
        return False


class LandlordAgentConversation(models.Model):
    """A conversation with one of the landlord AI agents."""

    AGENT_CHOICES = [
        ('pmm', 'Product Marketing Manager'),
        ('curriculum', 'Curriculum Analyst'),
        ('content', 'Content Creator'),
        ('seo', 'SEO Specialist & Brand Lead'),
    ]

    agent = models.CharField(max_length=20, choices=AGENT_CHOICES)
    title = models.CharField(max_length=200, default='New conversation')
    created_by = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE,
        related_name='landlord_conversations',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f'{self.get_agent_display()} — {self.title}'


class LandlordAgentMessage(models.Model):
    """A single message in a landlord agent conversation."""

    ROLE_CHOICES = [('user', 'User'), ('assistant', 'Assistant')]

    conversation = models.ForeignKey(
        LandlordAgentConversation, on_delete=models.CASCADE,
        related_name='messages',
    )
    role = models.CharField(max_length=12, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.role}: {self.content[:60]}'


class AgentSharedBrief(models.Model):
    """A knowledge artifact shared between landlord AI agents via the Briefing Room."""

    CATEGORY_CHOICES = [
        ('insight', 'Key Insight'),
        ('decision', 'Decision Made'),
        ('asset', 'Content Asset'),
        ('request', 'Request for Input'),
        ('data', 'Data / Analysis'),
    ]

    title = models.CharField(max_length=200)
    content = models.TextField(help_text='The shared knowledge or artifact')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='insight')
    source_agent = models.CharField(
        max_length=20, choices=LandlordAgentConversation.AGENT_CHOICES,
        help_text='Which agent produced this brief',
    )
    source_conversation = models.ForeignKey(
        LandlordAgentConversation, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='shared_briefs',
    )
    pinned = models.BooleanField(default=False, help_text='Pinned briefs always appear in agent context')
    created_by = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE,
        related_name='agent_shared_briefs',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-pinned', '-created_at']
        verbose_name = 'Agent Shared Brief'

    def __str__(self):
        return f'[{self.get_source_agent_display()}] {self.title}'


class PromoBanner(models.Model):
    """In-app promotional banner pushed from landlord agents to tenant dashboards."""

    STYLE_CHOICES = [
        ('gradient', 'Gradient'),
        ('glass', 'Glass'),
        ('bold', 'Bold'),
        ('minimal', 'Minimal'),
    ]
    AUDIENCE_CHOICES = [
        ('all', 'All Schools'),
        ('admins', 'School Admins'),
        ('teachers', 'Teachers'),
        ('students', 'Students'),
        ('parents', 'Parents'),
        ('landlord', 'Platform Admins'),
    ]

    headline = models.CharField(max_length=120)
    body = models.CharField(max_length=300, blank=True, default='')
    cta_text = models.CharField(max_length=40, default='Learn More')
    cta_link = models.CharField(max_length=500, blank=True, default='')
    style = models.CharField(max_length=12, choices=STYLE_CHOICES, default='gradient')
    audience = models.CharField(max_length=12, choices=AUDIENCE_CHOICES, default='all')
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    source_agent = models.CharField(max_length=20, blank=True, default='')
    created_by = models.ForeignKey(
        get_user_model(), on_delete=models.SET_NULL,
        null=True, blank=True, related_name='promo_banners',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Promo Banner'

    def __str__(self):
        return self.headline


class PromoBannerDismissal(models.Model):
    """Tracks when a user dismisses a promo banner — prevents it from reappearing."""
    banner = models.ForeignKey(PromoBanner, on_delete=models.CASCADE, related_name='dismissals')
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='dismissed_promos')
    dismissed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['banner', 'user']


class PromoBannerEvent(models.Model):
    """Tracks impressions and clicks on promo banners for analytics."""
    EVENT_TYPES = [('impression', 'Impression'), ('click', 'Click')]

    banner = models.ForeignKey(PromoBanner, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=12, choices=EVENT_TYPES)
    user = models.ForeignKey(
        get_user_model(), on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    tenant_schema = models.CharField(max_length=63, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['banner', 'event_type']),
            models.Index(fields=['created_at']),
        ]


class SocialMediaPost(models.Model):
    """Stores social media post content created by the Content Creator agent."""
    PLATFORM_CHOICES = [
        ('linkedin', 'LinkedIn'),
        ('x', 'X (Twitter)'),
        ('instagram', 'Instagram'),
        ('facebook', 'Facebook'),
        ('whatsapp', 'WhatsApp'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('published', 'Published'),
    ]

    day = models.PositiveSmallIntegerField(help_text='Day number in campaign')
    campaign = models.CharField(max_length=120, default='Launch Campaign')
    theme = models.CharField(max_length=120, help_text='Day theme e.g. Intro / value prop')
    platform = models.CharField(max_length=16, choices=PLATFORM_CHOICES)
    headline = models.CharField(max_length=200, blank=True, default='')
    hook = models.CharField(max_length=200, blank=True, default='')
    copy = models.TextField()
    cta = models.CharField(max_length=200, blank=True, default='')
    cta_link = models.CharField(max_length=500, blank=True, default='')
    image_note = models.CharField(max_length=300, blank=True, default='', help_text='Image/visual brief')
    hashtags = models.CharField(max_length=300, blank=True, default='')
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='draft')
    source_agent = models.CharField(max_length=20, blank=True, default='content')
    created_by = models.ForeignKey(
        get_user_model(), on_delete=models.SET_NULL,
        null=True, blank=True, related_name='social_posts',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['day', 'platform']
        verbose_name = 'Social Media Post'

    def __str__(self):
        return f'Day {self.day} — {self.get_platform_display()} — {self.theme}'


# Import subscription models
from .subscription_models import (
    SubscriptionPlan, AddOn, SchoolSubscription,
    SchoolAddOn, Invoice, ChurnEvent, AIUsageLog,
)

from .health_models import (
    SystemHealthMetric, SupportTicket, TicketComment, DatabaseBackup
)
