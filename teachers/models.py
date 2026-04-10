# teachers/models.py
import uuid
from django.db import models
from accounts.models import User

class Teacher(models.Model):
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )

    LANGUAGE_CHOICES = (
        ('english', 'English'),
        ('twi', 'Twi / Akan'),
        ('hausa', 'Hausa'),
        ('ewe', 'Ewe'),
        ('ga', 'Ga'),
        ('dagbani', 'Dagbani'),
        ('french', 'French'),
        ('other', 'Other'),
    )

    GHANA_REGIONS = (
        ('greater_accra', 'Greater Accra'),
        ('ashanti', 'Ashanti'),
        ('central', 'Central'),
        ('western', 'Western'),
        ('eastern', 'Eastern'),
        ('volta', 'Volta'),
        ('oti', 'Oti'),
        ('bono', 'Bono'),
        ('bono_east', 'Bono East'),
        ('ahafo', 'Ahafo'),
        ('northern', 'Northern'),
        ('north_east', 'North East'),
        ('savannah', 'Savannah'),
        ('upper_east', 'Upper East'),
        ('upper_west', 'Upper West'),
        ('western_north', 'Western North'),
        ('other', 'Other / Outside Ghana'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=20, unique=True)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='male', blank=True)
    date_of_joining = models.DateField()
    qualification = models.CharField(max_length=200)
    subjects = models.ManyToManyField('academics.Subject', blank=True)

    # Location & demographic fields
    region = models.CharField(
        max_length=50, choices=GHANA_REGIONS, blank=True, default='',
        help_text="Region where the teacher is currently based / teaches"
    )
    city = models.CharField(
        max_length=100, blank=True, default='',
        help_text="Town or city of current residence/posting"
    )
    hometown = models.CharField(
        max_length=150, blank=True, default='',
        help_text="Teacher's hometown / town of origin (informs cultural context)"
    )
    preferred_language = models.CharField(
        max_length=20, choices=LANGUAGE_CHOICES, default='english', blank=True,
        help_text="Teacher's primary spoken language"
    )

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id})"

class DutyWeek(models.Model):
    TERM_CHOICES = (
        ('first', 'First Term'),
        ('second', 'Second Term'),
        ('third', 'Third Term'),
    )
    academic_year = models.ForeignKey('academics.AcademicYear', on_delete=models.CASCADE)
    term = models.CharField(max_length=15, choices=TERM_CHOICES)
    week_number = models.PositiveIntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['start_date']
        unique_together = ['academic_year', 'term', 'week_number']
        verbose_name = "Duty Week"
        verbose_name_plural = "Duty Weeks"

    def __str__(self):
        return f"Week {self.week_number} ({self.start_date} - {self.end_date})"

class DutyAssignment(models.Model):
    week = models.ForeignKey(DutyWeek, on_delete=models.CASCADE, related_name='assignments')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    role = models.CharField(max_length=100, default="Member", help_text="e.g. Senior Team Leader, Member")
    
    class Meta:
        unique_together = ['week', 'teacher']
        ordering = ['role', 'teacher']

    def __str__(self):
        return f"{self.teacher} - {self.role}"

class LessonPlan(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='lesson_plans')
    subject = models.ForeignKey('academics.Subject', on_delete=models.CASCADE)
    school_class = models.ForeignKey('academics.Class', on_delete=models.CASCADE, verbose_name="Class")
    week_number = models.PositiveIntegerField()
    topic = models.CharField(max_length=200, verbose_name="Strand")
    sub_strand = models.CharField(max_length=255, blank=True, default='', verbose_name="Sub Strand")
    objectives = models.TextField(help_text="Specific learning outcomes")
    teaching_materials = models.TextField(blank=True, help_text="Materials needed for the lesson")
    
    # Lesson Procedure
    introduction = models.TextField(blank=True)
    presentation = models.TextField(blank=True, help_text="Main teaching activity")
    evaluation = models.TextField(blank=True, help_text="How students will be assessed")
    homework = models.TextField(blank=True)
    remarks = models.TextField(blank=True, help_text="Teacher reflection / PHASE 3 notes")
    
    date_added = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    share_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    b7_meta = models.JSONField(default=dict, blank=True, help_text="Extra editable fields for B7 weekly template (period, strand, hidden rows, etc.)")

    class Meta:
        ordering = ['-week_number', '-date_added']
    
    def __str__(self):
        return f"Week {self.week_number}: {self.subject} - {self.topic}"

class Presentation(models.Model):
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
        ('swirl', 'Swirl'),
        ('drop',  'Drop'),
    ]
    teacher      = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='presentations')
    title        = models.CharField(max_length=200)
    subject      = models.ForeignKey('academics.Subject', on_delete=models.SET_NULL, null=True, blank=True)
    school_class = models.ForeignKey('academics.Class',   on_delete=models.SET_NULL, null=True, blank=True)
    theme        = models.CharField(max_length=20, choices=THEME_CHOICES, default='aurora')
    transition   = models.CharField(max_length=20, choices=TRANSITION_CHOICES, default='slide')
    share_token  = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)
    times_presented  = models.PositiveIntegerField(default=0)
    last_presented_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title

    @property
    def slide_count(self):
        return self.slides.count()


class Slide(models.Model):
    LAYOUT_CHOICES = [
        ('title',    'Title Slide'),
        ('bullets',  'Bullet List'),
        ('two_col',  'Two Column'),
        ('big_stat', 'Big Stat'),
        ('quote',    'Quote'),
        ('summary',  'Summary'),
        ('image',    'Image + Caption'),
        ('poll',     'Live Poll'),
        ('quiz',     'Quiz Reveal'),
        ('video',    'Embedded Video'),
    ]
    presentation  = models.ForeignKey(Presentation, on_delete=models.CASCADE, related_name='slides')
    order         = models.PositiveIntegerField(default=0)
    layout        = models.CharField(max_length=20, choices=LAYOUT_CHOICES, default='bullets')
    title         = models.CharField(max_length=300, blank=True)
    content       = models.TextField(blank=True)   # newline-separated bullets or plain text
    speaker_notes = models.TextField(blank=True)
    emoji         = models.CharField(max_length=10, blank=True)
    image_url     = models.TextField(blank=True)   # data URI or hosted URL for image layout

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Slide {self.order + 1}: {self.title[:60]}"

    @property
    def bullets(self):
        return [b.strip() for b in self.content.split('\n') if b.strip()]


class LessonGenerationSession(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='ai_sessions')
    title = models.CharField(max_length=200, default="New Session")
    messages = models.JSONField(default=list)  # Stores list of {"role": "...", "content": "..."}
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.title} ({self.updated_at:%Y-%m-%d})"


class LiveSession(models.Model):
    """A live classroom session tied to a presentation deck."""
    presentation = models.ForeignKey(Presentation, on_delete=models.CASCADE, related_name='live_sessions')
    code = models.CharField(max_length=8, unique=True)
    is_active = models.BooleanField(default=True)
    current_slide_order = models.IntegerField(default=0)
    slide_time_data     = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Session {self.code} ({'active' if self.is_active else 'ended'})"


class PollResponse(models.Model):
    """A student's vote on a poll/quiz slide within a live session."""
    session = models.ForeignKey(LiveSession, on_delete=models.CASCADE, related_name='responses')
    slide = models.ForeignKey(Slide, on_delete=models.CASCADE, related_name='poll_responses')
    student_name = models.CharField(max_length=100, blank=True, default='Anonymous')
    choice = models.CharField(max_length=1)  # A, B, C, D
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('session', 'slide', 'student_name')]

    def __str__(self):
        return f"{self.student_name}: {self.choice} on slide {self.slide_id}"


# ---------------------------------------------------------------------------
# Teacher Add-On Store
# ---------------------------------------------------------------------------

class TeacherAddOn(models.Model):
    """Catalog item: a tool or resource pack teachers can purchase."""

    CATEGORY_CHOICES = [
        ('productivity', 'Productivity'),
        ('ai_tools', 'AI Tools'),
        ('assessment', 'Assessment'),
        ('content', 'Content Packs'),
        ('professional', 'Professional Dev'),
        ('classroom', 'Classroom Tools'),
    ]

    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    tagline = models.CharField(max_length=200, blank=True, default='')
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    icon = models.CharField(max_length=50, default='bi-box-seam', help_text='Bootstrap icon class')
    badge_label = models.CharField(max_length=30, blank=True, default='', help_text='e.g. "NEW", "POPULAR"')

    # Pricing
    price = models.DecimalField(max_digits=8, decimal_places=2, help_text='One-time price in school currency')
    is_free = models.BooleanField(default=False)
    trial_days = models.PositiveIntegerField(default=0, help_text='Free trial period in days (0 = no trial)')

    # Feature bullets (stored as JSON list of strings)
    features = models.JSONField(default=list, blank=True, help_text='["Feature 1","Feature 2",…]')

    # AI quota boost — purchasing this add-on adds extra monthly AI calls to school pool
    quota_boost = models.PositiveIntegerField(
        default=0,
        help_text='Extra monthly AI calls added to school quota when purchased (0 = no boost)',
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'price']

    def __str__(self):
        return self.name


class TeacherAddOnPurchase(models.Model):
    """Records a teacher's purchase of an add-on."""

    teacher = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, related_name='addon_purchases',
    )
    addon = models.ForeignKey(TeacherAddOn, on_delete=models.PROTECT, related_name='purchases')
    purchased_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text='Null = never expires')
    payment_reference = models.CharField(max_length=100, blank=True, default='')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        unique_together = ['teacher', 'addon']
        ordering = ['-purchased_at']

    def __str__(self):
        return f"{self.teacher.get_full_name()} → {self.addon.name}"


class DashboardPin(models.Model):
    """Pins a purchased add-on to the teacher's dashboard."""
    teacher = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='dashboard_pins')
    addon = models.ForeignKey(TeacherAddOn, on_delete=models.CASCADE, related_name='pins')
    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['teacher', 'addon']
        ordering = ['position', 'created_at']

    def __str__(self):
        return f"Pin: {self.addon.name}"


class QuickAction(models.Model):
    """A customisable quick-action button on the teacher dashboard."""
    teacher = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='quick_actions')
    label = models.CharField(max_length=60)
    icon = models.CharField(max_length=50, default='bi-lightning-charge')
    url_name = models.CharField(max_length=120, help_text='Django URL name, e.g. teachers:enter_grades')
    color = models.CharField(max_length=80, default='#4361ee', help_text='CSS color or gradient')
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['position']

    def __str__(self):
        return self.label


# ---------------------------------------------------------------------------
# Credit-Based Token System
# ---------------------------------------------------------------------------

class CreditPack(models.Model):
    """A purchasable pack of AI credits."""
    name = models.CharField(max_length=80)
    slug = models.SlugField(unique=True)
    credits = models.PositiveIntegerField(help_text='Number of credits in this pack')
    price = models.DecimalField(max_digits=8, decimal_places=2, help_text='Price in school currency (GHS)')
    badge_label = models.CharField(max_length=30, blank=True, default='')
    icon = models.CharField(max_length=50, default='bi-lightning-charge')
    is_active = models.BooleanField(default=True)
    position = models.PositiveIntegerField(default=0, help_text='Display order')

    class Meta:
        ordering = ['position', 'price']

    def __str__(self):
        return f"{self.name} ({self.credits} credits — GHS {self.price})"

    @property
    def price_per_credit(self):
        if self.credits:
            return self.price / self.credits
        return 0


class TeacherCreditBalance(models.Model):
    """Per-teacher credit balance — one row per teacher."""
    teacher = models.OneToOneField(
        'accounts.User', on_delete=models.CASCADE, related_name='credit_balance',
    )
    balance = models.IntegerField(default=0, help_text='Current available credits')
    total_purchased = models.PositiveIntegerField(default=0, help_text='Lifetime credits purchased')
    total_used = models.PositiveIntegerField(default=0, help_text='Lifetime credits consumed')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.teacher.get_full_name()} — {self.balance} credits"


class CreditTransaction(models.Model):
    """Audit log of every credit change."""
    TRANSACTION_TYPES = [
        ('purchase', 'Purchase'),
        ('usage', 'AI Usage'),
        ('bonus', 'Bonus / Welcome'),
        ('refund', 'Refund'),
    ]

    teacher = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, related_name='credit_transactions',
    )
    amount = models.IntegerField(help_text='Positive = added, negative = deducted')
    balance_after = models.IntegerField(help_text='Balance after this transaction')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.CharField(max_length=255)
    payment_reference = models.CharField(max_length=100, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        sign = '+' if self.amount > 0 else ''
        return f"{self.teacher.get_full_name()} {sign}{self.amount} ({self.transaction_type})"


# ---------------------------------------------------------------------------
# Add-on feature models
# ---------------------------------------------------------------------------

class TaskCard(models.Model):
    """Kanban card for the Task Board add-on."""
    COLUMN_CHOICES = [('todo', 'To Do'), ('doing', 'In Progress'), ('done', 'Done')]
    PRIORITY_CHOICES = [('low', 'Low'), ('medium', 'Medium'), ('high', 'High')]

    teacher = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='task_cards')
    title = models.CharField(max_length=200)
    column = models.CharField(max_length=10, choices=COLUMN_CHOICES, default='todo')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    due_date = models.DateField(null=True, blank=True)
    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['column', 'position', '-created_at']

    def __str__(self):
        return self.title


class CPDEntry(models.Model):
    """Continuing Professional Development log entry."""
    CATEGORY_CHOICES = [
        ('workshop', 'Workshop'), ('course', 'Course'),
        ('conference', 'Conference'), ('self_study', 'Self-Study'),
        ('mentoring', 'Mentoring'), ('other', 'Other'),
    ]
    teacher = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='cpd_entries')
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='workshop')
    hours = models.DecimalField(max_digits=5, decimal_places=1)
    date = models.DateField()
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.title} ({self.hours}h)"


class ObservationNote(models.Model):
    """Classroom observation note for peer review / mentoring."""
    teacher = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='observation_notes')
    observed_class = models.ForeignKey('academics.Class', on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField()
    strengths = models.TextField(blank=True, default='')
    growth_areas = models.TextField(blank=True, default='')
    action_plan = models.TextField(blank=True, default='')
    is_private = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Observation {self.date}"


class Rubric(models.Model):
    """Assessment rubric with JSON criteria rows."""
    teacher = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='rubrics')
    title = models.CharField(max_length=200)
    subject = models.ForeignKey('academics.Subject', on_delete=models.SET_NULL, null=True, blank=True)
    criteria = models.JSONField(default=list, help_text='[{"name":"…","levels":["Excellent","Good","Fair","Poor"]}]')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title


class StudyGuide(models.Model):
    """AI-generated study guide from lesson content."""
    teacher = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='study_guides')
    title = models.CharField(max_length=200)
    subject = models.ForeignKey('academics.Subject', on_delete=models.SET_NULL, null=True, blank=True)
    target_class = models.ForeignKey('academics.Class', on_delete=models.SET_NULL, null=True, blank=True)
    content_html = models.TextField(blank=True, default='')
    source_notes = models.TextField(blank=True, default='', help_text='Teacher notes used to generate guide')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


# ---------------------------------------------------------------------------
# New Add-on Feature Models (Wave 2)
# ---------------------------------------------------------------------------

class ReportCardComment(models.Model):
    """AI-generated end-of-term report card comments for a batch of students."""
    teacher = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='report_card_comments')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='report_comments')
    academic_year = models.ForeignKey('academics.AcademicYear', on_delete=models.CASCADE)
    term = models.CharField(max_length=10, choices=[('first', 'First Term'), ('second', 'Second Term'), ('third', 'Third Term')])
    comment = models.TextField(help_text='AI-generated or teacher-edited report comment')
    conduct = models.CharField(max_length=50, blank=True, default='')
    attitude = models.CharField(max_length=50, blank=True, default='')
    is_edited = models.BooleanField(default=False, help_text='True if teacher manually edited the AI output')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['student', 'academic_year', 'term']

    def __str__(self):
        return f"Report – {self.student} ({self.term} {self.academic_year})"


class QuestionBank(models.Model):
    """A categorised bank of exam questions."""
    DIFFICULTY_CHOICES = [('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')]
    FORMAT_CHOICES = [
        ('mcq', 'Multiple Choice'),
        ('fill', 'Fill in the Blank'),
        ('short', 'Short Answer'),
        ('essay', 'Essay'),
        ('truefalse', 'True / False'),
    ]
    BLOOM_CHOICES = [
        ('knowledge', 'Knowledge'),
        ('comprehension', 'Comprehension'),
        ('application', 'Application'),
        ('analysis', 'Analysis'),
        ('synthesis', 'Synthesis / Evaluation'),
    ]

    teacher = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='question_bank')
    subject = models.ForeignKey('academics.Subject', on_delete=models.SET_NULL, null=True, blank=True)
    target_class = models.ForeignKey('academics.Class', on_delete=models.SET_NULL, null=True, blank=True)
    topic = models.CharField(max_length=200, blank=True, default='')
    strand = models.CharField(max_length=200, blank=True, default='', help_text='GES strand e.g. Number, Algebra')
    sub_strand = models.CharField(max_length=200, blank=True, default='', help_text='GES sub-strand e.g. Number Operations')
    indicator_code = models.CharField(max_length=30, blank=True, default='', help_text='NaCCA indicator e.g. B7.1.1.1.1')
    bloom_level = models.CharField(max_length=15, choices=BLOOM_CHOICES, blank=True, default='', help_text="Bloom's taxonomy level")
    question_text = models.TextField()
    question_format = models.CharField(max_length=12, choices=FORMAT_CHOICES, default='mcq')
    difficulty = models.CharField(max_length=8, choices=DIFFICULTY_CHOICES, default='medium')
    options = models.JSONField(default=list, blank=True, help_text='["A) …","B) …","C) …","D) …"] for MCQs')
    correct_answer = models.TextField(blank=True, default='')
    explanation = models.TextField(blank=True, default='', help_text='Why the answer is correct')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.question_text[:80]


class ExamPaper(models.Model):
    """A generated exam paper composed from QuestionBank items."""
    teacher = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='exam_papers')
    title = models.CharField(max_length=200)
    subject = models.ForeignKey('academics.Subject', on_delete=models.SET_NULL, null=True, blank=True)
    target_class = models.ForeignKey('academics.Class', on_delete=models.SET_NULL, null=True, blank=True)
    questions = models.ManyToManyField(QuestionBank, blank=True, related_name='papers')
    duration_minutes = models.PositiveIntegerField(default=60)
    instructions = models.TextField(blank=True, default='Answer ALL questions.')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class BehaviorLog(models.Model):
    """Tracks student behavior events (positive and negative) and SEL check-ins."""
    TYPE_CHOICES = [('positive', 'Positive'), ('negative', 'Negative'), ('sel', 'SEL Check-in')]
    CATEGORY_CHOICES = [
        ('participation', 'Participation'), ('respect', 'Respect'),
        ('homework', 'Homework'), ('punctuality', 'Punctuality'),
        ('disruption', 'Disruption'), ('bullying', 'Bullying'),
        ('achievement', 'Achievement'), ('kindness', 'Kindness'),
        ('anxiety', 'Anxiety'), ('withdrawal', 'Withdrawal'),
        ('other', 'Other'),
    ]

    teacher = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='behavior_logs')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='behavior_logs')
    log_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='positive')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    note = models.TextField(blank=True, default='')
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.get_log_type_display()} – {self.student} ({self.date})"


class DifferentiatedLesson(models.Model):
    """AI-generated differentiated versions of a lesson plan."""
    teacher = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='differentiated_lessons')
    source_plan = models.ForeignKey(LessonPlan, on_delete=models.SET_NULL, null=True, blank=True, related_name='differentiated')
    title = models.CharField(max_length=200)
    subject = models.ForeignKey('academics.Subject', on_delete=models.SET_NULL, null=True, blank=True)
    target_class = models.ForeignKey('academics.Class', on_delete=models.SET_NULL, null=True, blank=True)
    foundational_html = models.TextField(blank=True, default='', help_text='For struggling learners')
    grade_level_html = models.TextField(blank=True, default='', help_text='For on-track learners')
    extension_html = models.TextField(blank=True, default='', help_text='For advanced learners')
    source_content = models.TextField(blank=True, default='', help_text='Original lesson or topic text')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class LiveQuiz(models.Model):
    """A live quiz session teachers can run in class."""
    teacher = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='live_quizzes')
    title = models.CharField(max_length=200)
    subject = models.ForeignKey('academics.Subject', on_delete=models.SET_NULL, null=True, blank=True)
    target_class = models.ForeignKey('academics.Class', on_delete=models.SET_NULL, null=True, blank=True)
    join_code = models.CharField(max_length=8, unique=True, blank=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.join_code:
            import random, string
            self.join_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        super().save(*args, **kwargs)


class LiveQuizQuestion(models.Model):
    """A question within a live quiz."""
    quiz = models.ForeignKey(LiveQuiz, on_delete=models.CASCADE, related_name='questions')
    order = models.PositiveIntegerField(default=0)
    text = models.TextField()
    option_a = models.CharField(max_length=300)
    option_b = models.CharField(max_length=300)
    option_c = models.CharField(max_length=300, blank=True, default='')
    option_d = models.CharField(max_length=300, blank=True, default='')
    correct = models.CharField(max_length=1, default='A')
    time_limit = models.PositiveIntegerField(default=30, help_text='Seconds per question')

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.text[:80]


class LiveQuizResponse(models.Model):
    """A participant's response to a quiz question."""
    question = models.ForeignKey(LiveQuizQuestion, on_delete=models.CASCADE, related_name='responses')
    player_name = models.CharField(max_length=100)
    choice = models.CharField(max_length=1)
    is_correct = models.BooleanField(default=False)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['question', 'player_name']

    def __str__(self):
        return f"{self.player_name}: {self.choice}"
