import secrets
import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


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
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Individual Profile'
        verbose_name_plural = 'Individual Profiles'

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
        raw = 'aura_' + secrets.token_hex(24)  # 53-char key
        prefix = raw[:8]
        hashed = hashlib.sha256(raw.encode()).hexdigest()
        return raw, prefix, hashed

    @staticmethod
    def hash_key(raw_key):
        import hashlib
        return hashlib.sha256(raw_key.encode()).hexdigest()


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
