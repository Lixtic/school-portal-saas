import secrets
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
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Individual Profile'
        verbose_name_plural = 'Individual Profiles'

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}"


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
    duration_minutes = models.PositiveIntegerField(default=40)
    objectives = models.TextField(blank=True, default='')
    materials = models.TextField(blank=True, default='')
    introduction = models.TextField(blank=True, default='')
    development = models.TextField(blank=True, default='')
    assessment = models.TextField(blank=True, default='')
    closure = models.TextField(blank=True, default='')
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Tool Lesson Plan'
        verbose_name_plural = 'Tool Lesson Plans'

    def __str__(self):
        return self.title
