import secrets
import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


class IndividualAddon(models.Model):
    """DB-stored catalog item for the individual addon store.
    Mirrors TeacherAddOn from teachers app so super admins can manage prices."""

    CATEGORY_CHOICES = [
        ('ai', 'AI Tools'),
        ('analytics', 'Analytics'),
        ('management', 'Management'),
        ('finance', 'Finance'),
        ('communication', 'Communication'),
        ('documents', 'Documents'),
        ('assessment', 'Assessment'),
        ('productivity', 'Productivity'),
        ('professional', 'Professional Dev'),
        ('subject_tools', 'Subject Tools'),
    ]
    AUDIENCE_CHOICES = [
        ('all', 'All Users'),
        ('teacher', 'Teachers Only'),
        ('developer', 'Developers Only'),
    ]

    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    tagline = models.CharField(max_length=200, blank=True, default='')
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    audience = models.CharField(max_length=20, choices=AUDIENCE_CHOICES, default='all')
    icon = models.CharField(max_length=50, default='bi-box-seam', help_text='Bootstrap icon class')
    badge_label = models.CharField(max_length=30, blank=True, default='', help_text='e.g. "NEW", "POPULAR"')

    # Pricing stored as JSON: {"free": 0, "pro": 59.99}
    plans = models.JSONField(default=list, help_text='Ordered list of plan names, e.g. ["free","pro"]')
    prices = models.JSONField(default=dict, help_text='Map plan→price, e.g. {"free":0,"pro":59.99}')

    trial_days = models.PositiveIntegerField(default=0, help_text='Free trial period in days (0 = no trial)')
    features = models.JSONField(default=list, blank=True, help_text='["Feature 1","Feature 2",…]')

    is_active = models.BooleanField(default=True)
    position = models.PositiveIntegerField(default=0, help_text='Display order within category')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['position', 'category', 'name']
        verbose_name = 'Individual Addon'
        verbose_name_plural = 'Individual Addons'

    def __str__(self):
        return self.name

    @property
    def is_free(self):
        return all(v <= 0 for v in self.prices.values())


class IndividualProfile(models.Model):
    """Extended profile for individual (non-school) platform users."""
    ROLE_CHOICES = [
        ('developer', 'Developer'),
        ('teacher', 'Teacher'),
    ]
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='individual_profile',
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='developer', db_index=True)
    phone_number = models.CharField(max_length=20, blank=True, db_index=True)
    google_id = models.CharField(max_length=255, blank=True, db_index=True)
    avatar_url = models.URLField(blank=True)
    company = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    referral_code = models.CharField(max_length=12, unique=True, blank=True)
    referred_by = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='referrals',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Individual Profile'
        verbose_name_plural = 'Individual Profiles'

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = secrets.token_urlsafe(8)[:8].upper()
        super().save(*args, **kwargs)

    @property
    def is_verified(self):
        """True if the user verified via email, phone, or Google OAuth."""
        return self.email_verified or self.phone_verified or bool(self.google_id)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}"


class VerificationCode(models.Model):
    """Time-limited OTP code for email/phone signup verification."""
    METHOD_CHOICES = [('email', 'Email'), ('phone', 'Phone')]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='verification_codes',
    )
    code = models.CharField(max_length=6)
    method = models.CharField(max_length=10, choices=METHOD_CHOICES)
    attempts = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ['-created_at']

    def is_expired(self):
        return timezone.now() > self.expires_at


class AddonSubscription(models.Model):
    """Tracks which addons an individual user is subscribed to."""
    PLAN_CHOICES = [
        ('free', 'Free'),
        ('starter', 'Starter'),
        ('pro', 'Pro'),
        ('enterprise', 'Enterprise'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]
    profile = models.ForeignKey(
        IndividualProfile, on_delete=models.CASCADE, related_name='subscriptions',
    )
    addon_slug = models.CharField(max_length=80)
    addon_name = models.CharField(max_length=120)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='free')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True, default='')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        unique_together = ('profile', 'addon_slug')
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.addon_name} ({self.plan}) — {self.profile}"

    @property
    def is_active(self):
        if self.status != 'active':
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True


class APIKey(models.Model):
    """API keys for individual users to access addon marketplace endpoints."""
    profile = models.ForeignKey(
        IndividualProfile, on_delete=models.CASCADE, related_name='api_keys',
    )
    name = models.CharField(max_length=100, help_text='A label for this key')
    prefix = models.CharField(max_length=8, db_index=True, editable=False)
    hashed_key = models.CharField(max_length=128, editable=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    calls_today = models.PositiveIntegerField(default=0)
    calls_total = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'API Key'
        verbose_name_plural = 'API Keys'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.prefix}…)"

    @staticmethod
    def generate():
        """Generate a new API key. Returns (raw_key, prefix, hashed_key)."""
        import hashlib
        raw = 'padi_' + secrets.token_hex(24)  # 53-char key
        prefix = raw[:8]
        hashed = hashlib.sha256(raw.encode()).hexdigest()
        return raw, prefix, hashed

    @staticmethod
    def hash_key(raw_key):
        import hashlib
        return hashlib.sha256(raw_key.encode()).hexdigest()


# ── Credit System ────────────────────────────────────────────────────────────
# Mirrors the teacher credit system for individual portal users.


class IndividualCreditPack(models.Model):
    """A purchasable pack of AI credits for individual users."""
    name = models.CharField(max_length=80)
    slug = models.SlugField(unique=True)
    credits = models.PositiveIntegerField(help_text='Number of credits in this pack')
    price = models.DecimalField(max_digits=8, decimal_places=2, help_text='Price in GHS')
    badge_label = models.CharField(max_length=30, blank=True, default='')
    icon = models.CharField(max_length=50, default='bi-lightning-charge')
    is_active = models.BooleanField(default=True)
    position = models.PositiveIntegerField(default=0, help_text='Display order')

    class Meta:
        ordering = ['position', 'price']
        verbose_name = 'Individual Credit Pack'

    def __str__(self):
        return f"{self.name} ({self.credits} credits — GHS {self.price})"

    @property
    def price_per_credit(self):
        if self.credits:
            return self.price / self.credits
        return 0


class IndividualCreditBalance(models.Model):
    """Per-user credit balance for individual portal users."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='individual_credit_balance',
    )
    balance = models.IntegerField(default=0, help_text='Current available credits')
    total_purchased = models.PositiveIntegerField(default=0, help_text='Lifetime credits purchased')
    total_used = models.PositiveIntegerField(default=0, help_text='Lifetime credits consumed')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Individual Credit Balance'

    def __str__(self):
        return f"{self.user.get_full_name()} — {self.balance} credits"


class IndividualCreditTransaction(models.Model):
    """Audit log of every credit change for individual users."""
    TRANSACTION_TYPES = [
        ('purchase', 'Purchase'),
        ('usage', 'AI Usage'),
        ('bonus', 'Bonus / Welcome'),
        ('referral', 'Referral Bonus'),
        ('refund', 'Refund'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='individual_credit_transactions',
    )
    amount = models.IntegerField(help_text='Positive = added, negative = deducted')
    balance_after = models.IntegerField(help_text='Balance after this transaction')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.CharField(max_length=255)
    payment_reference = models.CharField(max_length=100, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Individual Credit Transaction'

    def __str__(self):
        sign = '+' if self.amount > 0 else ''
        return f"{self.user.get_full_name()} {sign}{self.amount} ({self.transaction_type})"


# ── Tool Models (Public Schema) ──────────────────────────────────────────────
# Standalone equivalents of tenant-side teacher tools, gated by AddonSubscription


class ToolQuestion(models.Model):
    """Question bank item for standalone teacher portal."""
    DIFFICULTY_CHOICES = [('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')]
    FORMAT_CHOICES = [
        ('mcq', 'Multiple Choice'),
        ('fill', 'Fill in the Blank'),
        ('short', 'Short Answer'),
        ('essay', 'Essay'),
        ('truefalse', 'True / False'),
    ]
    SUBJECT_CHOICES = [
        ('mathematics', 'Mathematics'),
        ('english', 'English Language'),
        ('science', 'Integrated Science'),
        ('social_studies', 'Social Studies'),
        ('computing', 'Computing / ICT'),
        ('french', 'French'),
        ('ghanaian_language', 'Ghanaian Language'),
        ('rme', 'Religious & Moral Education'),
        ('creative_arts', 'Creative Arts & Design'),
        ('career_tech', 'Career Technology'),
        ('history', 'History'),
        ('geography', 'Geography'),
        ('physics', 'Physics'),
        ('chemistry', 'Chemistry'),
        ('biology', 'Biology'),
        ('literature', 'Literature'),
        ('economics', 'Economics'),
        ('government', 'Government'),
        ('other', 'Other'),
    ]

    profile = models.ForeignKey(
        IndividualProfile, on_delete=models.CASCADE, related_name='tool_questions',
    )
    subject = models.CharField(max_length=30, choices=SUBJECT_CHOICES, default='mathematics')
    target_class = models.CharField(max_length=60, blank=True, default='')
    topic = models.CharField(max_length=200, blank=True, default='')
    question_text = models.TextField()
    question_format = models.CharField(max_length=12, choices=FORMAT_CHOICES, default='mcq')
    difficulty = models.CharField(max_length=8, choices=DIFFICULTY_CHOICES, default='medium')
    options = models.JSONField(default=list, blank=True, help_text='["A) …","B) …","C) …","D) …"] for MCQs')
    correct_answer = models.TextField(blank=True, default='')
    explanation = models.TextField(blank=True, default='', help_text='Why the answer is correct')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Tool Question'
        verbose_name_plural = 'Tool Questions'

    def __str__(self):
        return self.question_text[:80]


class ToolExamPaper(models.Model):
    """Exam paper composed from ToolQuestion items."""
    profile = models.ForeignKey(
        IndividualProfile, on_delete=models.CASCADE, related_name='tool_exam_papers',
    )
    title = models.CharField(max_length=200)
    subject = models.CharField(max_length=30, choices=ToolQuestion.SUBJECT_CHOICES, default='mathematics')
    target_class = models.CharField(max_length=60, blank=True, default='')
    questions = models.ManyToManyField(ToolQuestion, blank=True, related_name='papers')
    duration_minutes = models.PositiveIntegerField(default=60)
    instructions = models.TextField(blank=True, default='Answer ALL questions.')
    school_name = models.CharField(max_length=200, blank=True, default='', help_text='For paper header')
    term = models.CharField(max_length=30, blank=True, default='')
    academic_year = models.CharField(max_length=20, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Tool Exam Paper'
        verbose_name_plural = 'Tool Exam Papers'

    def __str__(self):
        return self.title


class ToolLessonPlan(models.Model):
    """AI-generated or manual lesson plan."""
    profile = models.ForeignKey(
        IndividualProfile, on_delete=models.CASCADE, related_name='tool_lesson_plans',
    )
    title = models.CharField(max_length=200)
    subject = models.CharField(max_length=30, choices=ToolQuestion.SUBJECT_CHOICES, default='mathematics')
    target_class = models.CharField(max_length=60, blank=True, default='')
    topic = models.CharField(max_length=200, blank=True, default='')
    indicator = models.CharField(max_length=300, blank=True, default='', help_text='GES target indicator code or statement')
    sub_strand = models.CharField(max_length=200, blank=True, default='')
    duration_minutes = models.PositiveIntegerField(default=40)
    objectives = models.TextField(blank=True, default='')
    materials = models.TextField(blank=True, default='')
    introduction = models.TextField(blank=True, default='')
    development = models.TextField(blank=True, default='')
    assessment = models.TextField(blank=True, default='')
    closure = models.TextField(blank=True, default='')
    notes = models.TextField(blank=True, default='')
    b7_meta = models.JSONField(blank=True, null=True, default=None, help_text='GES lesson metadata')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Tool Lesson Plan'
        verbose_name_plural = 'Tool Lesson Plans'

    def __str__(self):
        return self.title


# ── Slide Deck / Presentation ────────────────────────────────────────────────

class ToolPresentation(models.Model):
    """Standalone slide deck for the teacher portal."""
    THEME_CHOICES = [
        ('aurora',   'Aurora'),
        ('midnight', 'Midnight'),
        ('forest',   'Forest'),
        ('coral',    'Coral'),
        ('slate',    'Slate'),
        ('ocean',    'Ocean'),
        ('amber',    'Amber'),
        ('rose',     'Rose'),
    ]
    TRANSITION_CHOICES = [
        ('slide', 'Slide'),
        ('fade',  'Fade'),
        ('zoom',  'Zoom'),
        ('flip',  'Flip'),
    ]

    profile = models.ForeignKey(
        IndividualProfile, on_delete=models.CASCADE, related_name='tool_presentations',
    )
    title = models.CharField(max_length=200)
    subject = models.CharField(max_length=30, choices=ToolQuestion.SUBJECT_CHOICES, default='mathematics')
    target_class = models.CharField(max_length=60, blank=True, default='')
    theme = models.CharField(max_length=20, choices=THEME_CHOICES, default='aurora')
    transition = models.CharField(max_length=20, choices=TRANSITION_CHOICES, default='slide')
    share_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    times_presented = models.PositiveIntegerField(default=0)
    last_presented_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Tool Presentation'
        verbose_name_plural = 'Tool Presentations'

    def __str__(self):
        return self.title

    @property
    def slide_count(self):
        return self.slides.count()


class ToolSlide(models.Model):
    """Single slide within a presentation."""
    LAYOUT_CHOICES = [
        ('title',    'Title Slide'),
        ('bullets',  'Bullet List'),
        ('two_col',  'Two Column'),
        ('big_stat', 'Big Stat'),
        ('quote',    'Quote'),
        ('summary',  'Summary'),
        ('image',    'Image + Caption'),
    ]

    presentation = models.ForeignKey(
        ToolPresentation, on_delete=models.CASCADE, related_name='slides',
    )
    order = models.PositiveIntegerField(default=0)
    layout = models.CharField(max_length=20, choices=LAYOUT_CHOICES, default='bullets')
    title = models.CharField(max_length=300, blank=True)
    content = models.TextField(blank=True)
    speaker_notes = models.TextField(blank=True)
    emoji = models.CharField(max_length=10, blank=True)
    image_url = models.TextField(blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Slide {self.order + 1}: {self.title[:60]}"

    @property
    def bullets(self):
        return [b.strip() for b in self.content.split('\n') if b.strip()]


# ── GTLE Licensure Prep ─────────────────────────────────────────────────────

# ── AI Teaching Assistant ─────────────────────────────────────────────────────

class AITutorConversation(models.Model):
    """A single conversation thread with the AI Teaching Assistant."""
    MODE_CHOICES = [
        ('explain', 'Concept Explainer'),
        ('worksheet', 'Worksheet Generator'),
        ('feedback', 'Marking Feedback'),
        ('notes', 'Study Notes Creator'),
        ('general', 'General Assistant'),
    ]
    profile = models.ForeignKey(
        IndividualProfile, on_delete=models.CASCADE,
        related_name='ai_tutor_conversations',
    )
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='general')
    title = models.CharField(max_length=200, blank=True, default='')
    subject = models.CharField(
        max_length=30, choices=ToolQuestion.SUBJECT_CHOICES, blank=True, default='',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'AI Tutor Conversation'

    def __str__(self):
        return self.title or f'{self.get_mode_display()} — {self.created_at:%d %b %Y}'


class AITutorMessage(models.Model):
    """Single message within an AI Tutor conversation."""
    ROLE_CHOICES = [('user', 'User'), ('assistant', 'Assistant')]
    conversation = models.ForeignKey(
        AITutorConversation, on_delete=models.CASCADE, related_name='messages',
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.role}: {self.content[:60]}'


class LicensureQuestion(models.Model):
    """GTLE licensure exam practice / past question."""

    DOMAIN_CHOICES = [
        ('literacy', 'Literacy'),
        ('numeracy', 'Numeracy'),
        ('pedagogy', 'Pedagogical Knowledge'),
        ('management', 'Classroom Management'),
    ]
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    SOURCE_CHOICES = [
        ('gtle_2024', 'GTLE 2024'),
        ('gtle_2023', 'GTLE 2023'),
        ('gtle_2022', 'GTLE 2022'),
        ('gtle_2021', 'GTLE 2021'),
        ('gtle_2020', 'GTLE 2020'),
        ('practice', 'Practice'),
        ('ai_generated', 'AI Generated'),
    ]

    profile = models.ForeignKey(
        IndividualProfile, on_delete=models.CASCADE,
        related_name='licensure_questions',
    )
    domain = models.CharField(max_length=20, choices=DOMAIN_CHOICES)
    topic = models.CharField(max_length=200, blank=True, default='')
    difficulty = models.CharField(
        max_length=8, choices=DIFFICULTY_CHOICES, default='medium',
    )
    source = models.CharField(
        max_length=20, choices=SOURCE_CHOICES, default='practice',
    )
    question_text = models.TextField()
    option_a = models.CharField(max_length=500)
    option_b = models.CharField(max_length=500)
    option_c = models.CharField(max_length=500)
    option_d = models.CharField(max_length=500)
    correct_option = models.CharField(max_length=1)  # A / B / C / D
    explanation = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Licensure Question'

    @property
    def option_list(self):
        return [
            ('A', self.option_a),
            ('B', self.option_b),
            ('C', self.option_c),
            ('D', self.option_d),
        ]

    def __str__(self):
        return self.question_text[:80]


class LicensureQuizAttempt(models.Model):
    """A quiz/mock exam attempt by a teacher."""

    MODE_CHOICES = [
        ('practice', 'Practice'),
        ('timed', 'Timed Exam'),
        ('domain', 'Domain Focus'),
    ]

    profile = models.ForeignKey(
        IndividualProfile, on_delete=models.CASCADE,
        related_name='licensure_attempts',
    )
    mode = models.CharField(max_length=12, choices=MODE_CHOICES, default='practice')
    domain_filter = models.CharField(max_length=20, blank=True, default='')
    total_questions = models.PositiveIntegerField(default=0)
    correct_count = models.PositiveIntegerField(default=0)
    time_limit_minutes = models.PositiveIntegerField(default=0)
    time_spent_seconds = models.PositiveIntegerField(default=0)
    completed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Licensure Quiz Attempt'

    def __str__(self):
        return f"Quiz {self.pk} — {self.get_mode_display()} ({self.score_percent}%)"

    @property
    def score_percent(self):
        if self.total_questions == 0:
            return 0
        return round((self.correct_count / self.total_questions) * 100)

    @property
    def passed(self):
        return self.score_percent >= 50


class LicensureAnswer(models.Model):
    """Single answer within a quiz attempt."""

    attempt = models.ForeignKey(
        LicensureQuizAttempt, on_delete=models.CASCADE, related_name='answers',
    )
    question = models.ForeignKey(
        LicensureQuestion, on_delete=models.CASCADE,
    )
    selected_option = models.CharField(max_length=1, blank=True, default='')
    is_correct = models.BooleanField(default=False)
    time_spent_seconds = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['pk']
        unique_together = ('attempt', 'question')


# ── GES Letter Writer ────────────────────────────────────────────────────────

class GESLetter(models.Model):
    """A letter written or generated by a teacher, following GES standards."""
    CATEGORY_CHOICES = [
        ('posting', 'Posting / Transfer'),
        ('leave', 'Leave of Absence'),
        ('promotion', 'Promotion Request'),
        ('complaint', 'Complaint / Grievance'),
        ('permission', 'Permission Request'),
        ('resignation', 'Resignation'),
        ('recommendation', 'Recommendation'),
        ('report', 'Incident / Report'),
        ('introduction', 'Letter of Introduction'),
        ('request', 'General Request'),
        ('appreciation', 'Appreciation / Thank You'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('final', 'Final'),
    ]

    profile = models.ForeignKey(
        IndividualProfile, on_delete=models.CASCADE,
        related_name='ges_letters',
    )
    title = models.CharField(max_length=250)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='request')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    recipient_name = models.CharField(max_length=200, blank=True, default='')
    recipient_title = models.CharField(max_length=200, blank=True, default='',
                                       help_text='e.g. District Director of Education')
    sender_name = models.CharField(max_length=200, blank=True, default='')
    sender_title = models.CharField(max_length=200, blank=True, default='',
                                    help_text='e.g. Classroom Teacher')
    school_name = models.CharField(max_length=200, blank=True, default='')
    district = models.CharField(max_length=200, blank=True, default='')
    region = models.CharField(max_length=200, blank=True, default='')
    reference_number = models.CharField(max_length=100, blank=True, default='')
    date_written = models.DateField(null=True, blank=True)
    body = models.TextField(blank=True, default='')
    is_sample = models.BooleanField(default=False)
    ai_generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'GES Letter'
        verbose_name_plural = 'GES Letters'

    def __str__(self):
        return self.title


# ── Paper Marker ─────────────────────────────────────────────────────────────

class MarkingSession(models.Model):
    """A marking session for an objective (MCQ) question paper."""
    profile = models.ForeignKey(
        IndividualProfile, on_delete=models.CASCADE, related_name='marking_sessions',
    )
    title = models.CharField(max_length=250)
    subject = models.CharField(max_length=150, blank=True, default='')
    class_name = models.CharField(max_length=100, blank=True, default='',
                                  help_text='e.g. Basic 7, JHS 2')
    total_questions = models.PositiveIntegerField(default=40)
    options_per_question = models.PositiveIntegerField(default=4,
                                                       help_text='Number of options per question (e.g. 4 for A-D)')
    answer_key = models.JSONField(default=list, blank=True,
                                  help_text='List of correct answers e.g. ["A","B","C",...]')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title

    @property
    def student_count(self):
        return self.marks.count()

    @property
    def class_average(self):
        marks = self.marks.all()
        if not marks:
            return 0
        return round(sum(m.percentage for m in marks) / marks.count(), 1)


class StudentMark(models.Model):
    """Individual student result within a marking session."""
    session = models.ForeignKey(
        MarkingSession, on_delete=models.CASCADE, related_name='marks',
    )
    student_name = models.CharField(max_length=200)
    student_index = models.CharField(max_length=50, blank=True, default='',
                                     help_text='Student ID or index number')
    responses = models.JSONField(default=list, blank=True,
                                 help_text='List of student answers e.g. ["A","C","B",...]')
    score = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)
    percentage = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['student_name']

    def __str__(self):
        return f'{self.student_name} — {self.score}/{self.total}'

    def grade_responses(self):
        """Compare responses against session answer key and set score."""
        key = self.session.answer_key or []
        correct = 0
        for i, ans in enumerate(self.responses):
            if i < len(key) and str(ans).strip().upper() == str(key[i]).strip().upper():
                correct += 1
        self.score = correct
        self.total = len(key)
        self.percentage = round((correct / len(key)) * 100, 1) if key else 0


# ── Report Card Writer ────────────────────────────────────────────────────────

class ReportCardSet(models.Model):
    """A batch of report cards for one class / term."""
    TERM_CHOICES = [
        ('first', 'First Term'),
        ('second', 'Second Term'),
        ('third', 'Third Term'),
    ]
    profile = models.ForeignKey(
        IndividualProfile, on_delete=models.CASCADE, related_name='report_card_sets',
    )
    title = models.CharField(max_length=200)
    class_name = models.CharField(max_length=100)
    term = models.CharField(max_length=10, choices=TERM_CHOICES, default='first')
    academic_year = models.CharField(max_length=20, default='2025/2026')
    school_name = models.CharField(max_length=200, blank=True, default='')
    next_term_begins = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title


class ReportCardEntry(models.Model):
    """Individual student report card within a set."""
    RATING_CHOICES = [
        ('excellent', 'Excellent'),
        ('very_good', 'Very Good'),
        ('good', 'Good'),
        ('satisfactory', 'Satisfactory'),
        ('needs_improvement', 'Needs Improvement'),
    ]
    card_set = models.ForeignKey(
        ReportCardSet, on_delete=models.CASCADE, related_name='entries',
    )
    student_name = models.CharField(max_length=200)
    subjects = models.JSONField(
        default=list, blank=True,
        help_text='[{subject, class_score, exam_score, total, grade, remark}]',
    )
    overall_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    overall_grade = models.CharField(max_length=5, blank=True, default='')
    position = models.PositiveIntegerField(null=True, blank=True)
    total_students = models.PositiveIntegerField(null=True, blank=True)
    conduct = models.CharField(max_length=20, choices=RATING_CHOICES, default='good')
    attitude = models.CharField(max_length=20, choices=RATING_CHOICES, default='good')
    interest = models.CharField(max_length=20, choices=RATING_CHOICES, default='good')
    attendance = models.CharField(max_length=30, blank=True, default='')
    class_teacher_comment = models.TextField(blank=True, default='')
    head_teacher_comment = models.TextField(blank=True, default='')
    promoted = models.BooleanField(null=True, blank=True)
    next_class = models.CharField(max_length=100, blank=True, default='')
    ai_generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['student_name']

    def __str__(self):
        return f'{self.student_name} — {self.card_set.title}'


# ── Subject-Area Tools ───────────────────────────────────────────────────────

class CompuThinkActivity(models.Model):
    """Computational-thinking exercise generated for the Computing curriculum."""
    TYPE_CHOICES = [
        ('algorithm', 'Algorithm Design'),
        ('pseudocode', 'Pseudocode Writing'),
        ('pattern', 'Pattern Recognition'),
        ('decomposition', 'Decomposition'),
        ('abstraction', 'Abstraction'),
        ('coding', 'Coding Challenge'),
        ('ai_literacy', 'AI Literacy'),
        ('productivity', 'Digital Productivity'),
    ]
    LEVEL_CHOICES = [
        ('b7', 'Basic 7'),
        ('b8', 'Basic 8'),
        ('b9', 'Basic 9'),
        ('b10', 'Basic 10'),
        ('shs1', 'SHS 1'),
        ('shs2', 'SHS 2'),
        ('shs3', 'SHS 3'),
    ]

    profile = models.ForeignKey(
        IndividualProfile, on_delete=models.CASCADE,
        related_name='computhink_activities',
    )
    title = models.CharField(max_length=250)
    activity_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='algorithm')
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='b7')
    strand = models.CharField(max_length=100, blank=True, default='',
                              help_text='e.g. Computational Thinking, AI Literacy')
    topic = models.CharField(max_length=200, blank=True, default='')
    instructions = models.TextField(blank=True, default='')
    content = models.JSONField(
        default=dict, blank=True,
        help_text='Structured activity: {problem, steps, hints, expected_output, extension}',
    )
    answer_key = models.TextField(blank=True, default='')
    ai_generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'CompuThink Activity'
        verbose_name_plural = 'CompuThink Activities'

    def __str__(self):
        return self.title


class LiteracyExercise(models.Model):
    """English & Language Arts exercise — reading, grammar, vocabulary, writing."""
    TYPE_CHOICES = [
        ('comprehension', 'Reading Comprehension'),
        ('grammar', 'Grammar Drill'),
        ('vocabulary', 'Vocabulary Builder'),
        ('phonics', 'Phonics / Remedial'),
        ('essay', 'Essay / Creative Writing'),
        ('oral', 'Oral Language Activity'),
        ('literature', 'Literature Study'),
    ]
    LEVEL_CHOICES = CompuThinkActivity.LEVEL_CHOICES

    profile = models.ForeignKey(
        IndividualProfile, on_delete=models.CASCADE,
        related_name='literacy_exercises',
    )
    title = models.CharField(max_length=250)
    exercise_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='comprehension')
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='b7')
    strand = models.CharField(max_length=100, blank=True, default='',
                              help_text='e.g. Reading, Grammar, Writing')
    topic = models.CharField(max_length=200, blank=True, default='')
    passage = models.TextField(blank=True, default='',
                               help_text='Reading passage or source text')
    content = models.JSONField(
        default=dict, blank=True,
        help_text='Structured exercise: {questions, options, word_list, rubric, prompts}',
    )
    answer_key = models.TextField(blank=True, default='')
    ai_generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Literacy Exercise'
        verbose_name_plural = 'Literacy Exercises'

    def __str__(self):
        return self.title


class CitizenEdActivity(models.Model):
    """Social Studies activity — governance, culture, citizenship, environment."""
    TYPE_CHOICES = [
        ('case_study', 'Case Study'),
        ('debate', 'Debate / Discussion Prompt'),
        ('scenario', 'Citizenship Scenario'),
        ('map_activity', 'Map / Geography Activity'),
        ('timeline', 'Historical Timeline'),
        ('research', 'Research Project'),
        ('values', 'National Values Education'),
    ]
    LEVEL_CHOICES = CompuThinkActivity.LEVEL_CHOICES
    STRAND_CHOICES = [
        ('environment', 'Our Environment'),
        ('governance', 'Governance & Politics'),
        ('culture', 'Culture & Identity'),
        ('globalism', 'Globalism & International Relations'),
        ('citizenship', 'Responsible Citizenship'),
        ('economics', 'Economics & Development'),
    ]

    profile = models.ForeignKey(
        IndividualProfile, on_delete=models.CASCADE,
        related_name='citizen_ed_activities',
    )
    title = models.CharField(max_length=250)
    activity_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='case_study')
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='b7')
    strand = models.CharField(max_length=20, choices=STRAND_CHOICES, default='citizenship')
    topic = models.CharField(max_length=200, blank=True, default='')
    scenario_text = models.TextField(blank=True, default='',
                                     help_text='The case study, scenario or discussion prompt')
    content = models.JSONField(
        default=dict, blank=True,
        help_text='Structured activity: {questions, key_points, tasks, resources, rubric}',
    )
    answer_guide = models.TextField(blank=True, default='')
    ai_generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'CitizenEd Activity'
        verbose_name_plural = 'CitizenEd Activities'

    def __str__(self):
        return self.title


class TVETProject(models.Model):
    """Career Technology project — TVET-linked practical activities."""
    TYPE_CHOICES = [
        ('project_plan', 'Project Plan'),
        ('safety_quiz', 'Health & Safety Quiz'),
        ('tool_id', 'Tools & Materials ID'),
        ('innovation', 'Innovation Challenge'),
        ('rubric', 'Skill Assessment Rubric'),
        ('workshop', 'Workshop Activity'),
    ]
    LEVEL_CHOICES = CompuThinkActivity.LEVEL_CHOICES
    STRAND_CHOICES = [
        ('health_safety', 'Health & Safety'),
        ('materials', 'Materials & Processes'),
        ('tools', 'Tools & Equipment'),
        ('innovation', 'Innovation & Entrepreneurship'),
        ('design', 'Design & Technology'),
    ]

    profile = models.ForeignKey(
        IndividualProfile, on_delete=models.CASCADE,
        related_name='tvet_projects',
    )
    title = models.CharField(max_length=250)
    project_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='project_plan')
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='b7')
    strand = models.CharField(max_length=20, choices=STRAND_CHOICES, default='tools')
    topic = models.CharField(max_length=200, blank=True, default='')
    description = models.TextField(blank=True, default='')
    content = models.JSONField(
        default=dict, blank=True,
        help_text='Structured project: {objectives, materials, steps, safety_notes, assessment, extension}',
    )
    answer_key = models.TextField(blank=True, default='')
    ai_generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'TVET Project'
        verbose_name_plural = 'TVET Projects'

    def __str__(self):
        return self.title


# ── Grade Analytics ──────────────────────────────────────────────────────────

class GradeBook(models.Model):
    """A grade book for a class/subject — container for student grade entries."""
    TERM_CHOICES = [
        ('term_1', 'Term 1'),
        ('term_2', 'Term 2'),
        ('term_3', 'Term 3'),
    ]

    profile = models.ForeignKey(
        IndividualProfile, on_delete=models.CASCADE,
        related_name='grade_books',
    )
    title = models.CharField(max_length=250)
    subject = models.CharField(max_length=100, blank=True, default='')
    target_class = models.CharField(max_length=50, blank=True, default='')
    term = models.CharField(max_length=10, choices=TERM_CHOICES, default='term_1')
    academic_year = models.CharField(max_length=20, blank=True, default='')
    max_score = models.PositiveIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Grade Book'

    def __str__(self):
        return self.title

    @property
    def entry_count(self):
        return self.entries.count()

    @property
    def class_average(self):
        from django.db.models import Avg
        result = self.entries.aggregate(avg=Avg('score'))
        return round(result['avg'], 1) if result['avg'] is not None else 0


class GradeEntry(models.Model):
    """A single student's score in a grade book."""
    GRADE_CHOICES = [
        ('A', 'A — Excellent'),
        ('B', 'B — Very Good'),
        ('C', 'C — Good'),
        ('D', 'D — Satisfactory'),
        ('E', 'E — Below Average'),
        ('F', 'F — Fail'),
    ]

    grade_book = models.ForeignKey(
        GradeBook, on_delete=models.CASCADE, related_name='entries',
    )
    student_name = models.CharField(max_length=200)
    score = models.DecimalField(max_digits=5, decimal_places=1)
    grade = models.CharField(max_length=2, choices=GRADE_CHOICES, blank=True, default='')
    remarks = models.CharField(max_length=200, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['student_name']
        verbose_name = 'Grade Entry'
        verbose_name_plural = 'Grade Entries'

    def __str__(self):
        return f'{self.student_name} — {self.score}'

    def save(self, *args, **kwargs):
        # Auto-assign letter grade from score (percentage of max_score)
        if self.grade_book_id:
            max_s = self.grade_book.max_score or 100
            pct = (float(self.score) / max_s) * 100
            if pct >= 80:
                self.grade = 'A'
            elif pct >= 70:
                self.grade = 'B'
            elif pct >= 60:
                self.grade = 'C'
            elif pct >= 50:
                self.grade = 'D'
            elif pct >= 40:
                self.grade = 'E'
            else:
                self.grade = 'F'
        super().save(*args, **kwargs)


# ── Attendance Tracker ───────────────────────────────────────────────────────

class AttendanceRegister(models.Model):
    """A register for tracking attendance for a class."""

    profile = models.ForeignKey(
        IndividualProfile, on_delete=models.CASCADE,
        related_name='attendance_registers',
    )
    title = models.CharField(max_length=250)
    target_class = models.CharField(max_length=50, blank=True, default='')
    academic_year = models.CharField(max_length=20, blank=True, default='')
    students = models.JSONField(
        default=list, blank=True,
        help_text='List of student names: ["Ama Mensah", "Kofi Asare", ...]',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Attendance Register'

    def __str__(self):
        return self.title

    @property
    def student_count(self):
        return len(self.students) if self.students else 0

    @property
    def session_count(self):
        return self.sessions.count()


class AttendanceSession(models.Model):
    """A single day's attendance record."""
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
    ]

    register = models.ForeignKey(
        AttendanceRegister, on_delete=models.CASCADE, related_name='sessions',
    )
    date = models.DateField()
    records = models.JSONField(
        default=dict, blank=True,
        help_text='{"student_name": "present"|"absent"|"late"|"excused", ...}',
    )
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        unique_together = ['register', 'date']
        verbose_name = 'Attendance Session'

    def __str__(self):
        return f'{self.register.title} — {self.date}'

    @property
    def present_count(self):
        return sum(1 for v in (self.records or {}).values() if v == 'present')

    @property
    def absent_count(self):
        return sum(1 for v in (self.records or {}).values() if v == 'absent')
