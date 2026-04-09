from django.db import models
from accounts.models import User


def _clear_tenant_cache(prefix):
    """Invalidate the per-tenant cached value for this model."""
    try:
        from django.core.cache import cache
        from django.db import connection
        schema = getattr(connection, 'schema_name', 'public')
        cache.delete(f'{prefix}_{schema}')
    except Exception:
        pass


class AcademicYear(models.Model):
    name = models.CharField(max_length=20)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False, db_index=True)
    
    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        _clear_tenant_cache('current_academic_year')
    
    class Meta:
        ordering = ['-start_date']

class SchoolInfo(models.Model):
    name = models.CharField(max_length=200, default="School Name")
    address = models.TextField(default="School Address")
    phone = models.CharField(max_length=50, default="Phone Number")
    email = models.EmailField(default="info@school.edu")
    
    # Onboarding
    setup_complete = models.BooleanField(default=False)
    
    motto = models.CharField(max_length=200, default="Education for All")
    logo = models.ImageField(upload_to='school_logo/', null=True, blank=True)
    
    # Customization
    primary_color = models.CharField(max_length=7, default="#026e56", help_text="Main theme color (e.g. #026e56)")
    secondary_color = models.CharField(max_length=7, default="#0f3b57", help_text="Sidebar/Dark color (e.g. #0f3b57)")
    
    TEMPLATE_CHOICES = (
        ('default', 'Default (Activity Feed)'),
        ('modern', 'Modern (Hero + Highlights)'),
        ('classic', 'Classic (Sidebar + Info)'),
        ('minimal', 'Minimal (Centered Focus)'),
        ('playful', 'Playful (Colorful + Shapes)'),
        ('elegant', 'Elegant (Navy + Gold)'),
        ('artdeco', 'Art Deco (Bold Geometric)'),
        ('japandi', 'Japandi (Calm & Minimal)'),
    )
    homepage_template = models.CharField(max_length=20, choices=TEMPLATE_CHOICES, default='default')
    
    ID_CARD_TEMPLATE_CHOICES = (
        ('classic', 'Classic — Orange accent, clean layout'),
        ('modern', 'Modern — Gradient header, vibrant colors'),
        ('elegant', 'Elegant — Navy & gold, professional look'),
    )
    id_card_template = models.CharField(max_length=20, choices=ID_CARD_TEMPLATE_CHOICES, default='classic', help_text="ID card design template for students and teachers")

    REPORT_CARD_TEMPLATE_CHOICES = (
        ('classic', 'Classic — Traditional bordered report card'),
        ('modern_plus', 'Modern Plus — Contemporary gradient style'),
        ('minimal_clean', 'Minimal Clean — Lightweight monochrome style'),
    )
    report_card_template = models.CharField(max_length=20, choices=REPORT_CARD_TEMPLATE_CHOICES, default='classic', help_text="Report card design template")
    
    # Hero Section Customization
    hero_title = models.CharField(max_length=200, blank=True, default='', help_text="Main hero heading (leave empty to use school name)")
    hero_subtitle = models.CharField(max_length=300, blank=True, default='', help_text="Hero subtitle/description")
    cta_primary_text = models.CharField(max_length=50, default='Portal Login', help_text="Primary call-to-action button text")
    cta_primary_url = models.CharField(max_length=200, default='/login/', help_text="Primary CTA URL")
    cta_secondary_text = models.CharField(max_length=50, default='Apply Now', help_text="Secondary call-to-action button text")
    cta_secondary_url = models.CharField(max_length=200, default='/academics/apply/', help_text="Secondary CTA URL")
    
    # Stats Section
    stat1_number = models.CharField(max_length=20, default='25+', help_text="First statistic number")
    stat1_label = models.CharField(max_length=50, default='Years of Excellence', help_text="First statistic label")
    stat2_number = models.CharField(max_length=20, default='1000+', help_text="Second statistic number")
    stat2_label = models.CharField(max_length=50, default='Students Enrolled', help_text="Second statistic label")
    stat3_number = models.CharField(max_length=20, default='50+', help_text="Third statistic number")
    stat3_label = models.CharField(max_length=50, default='Expert Teachers', help_text="Third statistic label")
    stat4_number = models.CharField(max_length=20, default='98%', help_text="Fourth statistic number")
    stat4_label = models.CharField(max_length=50, default='Success Rate', help_text="Fourth statistic label")
    
    # Features/Highlights
    feature1_title = models.CharField(max_length=100, default='Academic Excellence', help_text="First feature title")
    feature1_description = models.TextField(default='Proven track record of outstanding academic performance and university placements.')
    feature1_icon = models.CharField(max_length=50, default='fa-award', help_text="FontAwesome icon class (e.g., fa-award)")
    feature2_title = models.CharField(max_length=100, default='Expert Faculty', help_text="Second feature title")
    feature2_description = models.TextField(default='Highly qualified and dedicated teachers committed to student success.')
    feature2_icon = models.CharField(max_length=50, default='fa-users', help_text="FontAwesome icon class")
    feature3_title = models.CharField(max_length=100, default='Modern Facilities', help_text="Third feature title")
    feature3_description = models.TextField(default='State-of-the-art classrooms, laboratories, and sports facilities.')
    feature3_icon = models.CharField(max_length=50, default='fa-building', help_text="FontAwesome icon class")
    
    # About Section
    about_title = models.CharField(max_length=100, default='Why Choose Us', help_text="About/Why Choose section title")
    about_description = models.TextField(blank=True, default='We provide a comprehensive educational experience that nurtures academic excellence, character development, and leadership skills.')
    
    # Social Media
    facebook_url = models.URLField(blank=True, default='', help_text="Facebook page URL")
    twitter_url = models.URLField(blank=True, default='', help_text="Twitter/X profile URL")
    instagram_url = models.URLField(blank=True, default='', help_text="Instagram profile URL")
    linkedin_url = models.URLField(blank=True, default='', help_text="LinkedIn page URL")
    youtube_url = models.URLField(blank=True, default='', help_text="YouTube channel URL")
    
    # Section Visibility
    show_stats_section = models.BooleanField(default=True, help_text="Display statistics section on homepage")
    show_programs_section = models.BooleanField(default=True, help_text="Display academic programs section")
    show_gallery_preview = models.BooleanField(default=True, help_text="Display gallery preview section")
    
    def save(self, *args, **kwargs):
        if not self.pk and SchoolInfo.objects.exists():
            # Singleton: reuse existing row instead of creating duplicate
            self.pk = SchoolInfo.objects.first().pk
        super().save(*args, **kwargs)
        _clear_tenant_cache('school_info')
    
    def get_safe(self, field_name, default=None):
        """Safely get field value with default fallback"""
        try:
            value = getattr(self, field_name, default)
            return value if value is not None else default
        except (AttributeError, Exception):
            return default

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "School Information"


class Class(models.Model):
    name = models.CharField(max_length=50)  # e.g., "Grade 10A", "Grade 9B"
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    class_teacher = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL, 
                                     null=True, blank=True, related_name='managed_classes')
    
    def __str__(self):
        return f"{self.name}"
    
    class Meta:
        verbose_name_plural = "Classes"
        unique_together = ['name', 'academic_year']


class Activity(models.Model):
    title = models.CharField(max_length=120)
    summary = models.TextField(blank=True)
    date = models.DateField()
    tag = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_activities')
    assigned_staff = models.ManyToManyField(User, blank=True, related_name='assigned_activities')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.date})"

    class Meta:
        ordering = ['date', '-created_at']
        indexes = [
            models.Index(fields=['is_active', 'date'], name='activity_active_date_idx'),
        ]


class SchoolEvent(models.Model):
    CATEGORY_CHOICES = (
        ('academic', 'Academic'),
        ('exam', 'Examination'),
        ('holiday', 'Holiday / Break'),
        ('sport', 'Sports & Games'),
        ('cultural', 'Cultural / Social'),
        ('meeting', 'Meeting'),
        ('pta', 'PTA / Parents'),
        ('other', 'Other'),
    )
    AUDIENCE_CHOICES = (
        ('all', 'Everyone'),
        ('admin', 'Admin Only'),
        ('teachers', 'Teachers'),
        ('students', 'Students'),
        ('parents', 'Parents'),
    )
    COLOR_MAP = {
        'academic': '#4361ee',
        'exam': '#ef4444',
        'holiday': '#10b981',
        'sport': '#f59e0b',
        'cultural': '#8b5cf6',
        'meeting': '#6366f1',
        'pta': '#ec4899',
        'other': '#64748b',
    }

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    date_start = models.DateField()
    date_end = models.DateField(null=True, blank=True, help_text='Leave blank for single-day events')
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    is_all_day = models.BooleanField(default=True)
    location = models.CharField(max_length=200, blank=True)
    audience = models.CharField(max_length=20, choices=AUDIENCE_CHOICES, default='all')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date_start', 'start_time']

    def __str__(self):
        return f"{self.title} ({self.date_start})"

    @property
    def color(self):
        return self.COLOR_MAP.get(self.category, '#64748b')

    @property
    def is_multi_day(self):
        return self.date_end and self.date_end > self.date_start


class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class ClassSubject(models.Model):
    class_name = models.ForeignKey(Class, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"{self.class_name} - {self.subject}"
    
    class Meta:
        unique_together = ['class_name', 'subject']


class Timetable(models.Model):
    DAY_CHOICES = (
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    )
    class_subject = models.ForeignKey(ClassSubject, on_delete=models.CASCADE)
    day = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=50, blank=True, help_text="e.g. Room 101 or Lab A")

    class Meta:
        ordering = ['day', 'start_time']
        verbose_name_plural = "Timetables"

    def __str__(self):
        try:
            day_name = self.get_day_display()
            return f"{self.class_subject} on {day_name} ({self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')})"
        except Exception:
            # Fallback if database access fails (e.g., broken transaction)
            return f"Timetable #{self.id}"


class GradingScale(models.Model):
    """Per-tenant configurable grading thresholds. Rows ordered by min_score DESC."""
    min_score = models.DecimalField(max_digits=5, decimal_places=2)
    grade_label = models.CharField(max_length=5, help_text="e.g. 1, A+, A")
    remarks = models.CharField(max_length=60)
    ordering = models.PositiveIntegerField(default=0, help_text="Lower = higher grade")

    class Meta:
        ordering = ['-min_score']
        verbose_name_plural = "Grading Scale"

    def __str__(self):
        return f"{self.grade_label} (≥{self.min_score}%) — {self.remarks}"


class ExamSchedule(models.Model):
    """Scheduled exam with date, time, room, and invigilator."""
    TERM_CHOICES = (
        ('first', 'First Term'),
        ('second', 'Second Term'),
        ('third', 'Third Term'),
    )

    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    term = models.CharField(max_length=10, choices=TERM_CHOICES)
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE)
    target_class = models.ForeignKey('Class', on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=80, blank=True, help_text="e.g. Hall A, Room 102")
    invigilator = models.ForeignKey(
        'teachers.Teacher', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='invigilator_duties',
    )
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'start_time']
        unique_together = ['target_class', 'subject', 'academic_year', 'term']

    def __str__(self):
        return f"{self.subject.name} — {self.target_class.name} ({self.date})"


class GalleryImage(models.Model):
    CATEGORY_CHOICES = [
        ('campus', 'Campus'),
        ('events', 'Events'),
        ('sports', 'Sports'),
        ('academics', 'Academics'),
        ('others', 'Others'),
    ]
    
    title = models.CharField(max_length=100)
    caption = models.TextField(blank=True)
    image = models.ImageField(upload_to='gallery/')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='events')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']

class Resource(models.Model):
    RESOURCE_TYPE_CHOICES = [
        ('curriculum', 'Curriculum'),
        ('teaching', 'Teaching Resource'),
    ]

    CURRICULUM_CHOICES = [
        ('ges_jhs_new', 'GES New Curriculum (JHS)'),
        ('ges_basic', 'GES Basic School'),
        ('waec_legacy', 'WAEC/Legacy'),
        ('cambridge_lower', 'Cambridge Lower Secondary'),
        ('other', 'Other/General'),
    ]

    class_subject = models.ForeignKey(ClassSubject, on_delete=models.CASCADE, related_name='resources', null=True, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPE_CHOICES, default='teaching')
    curriculum = models.CharField(max_length=50, choices=CURRICULUM_CHOICES, default='ges_jhs_new')
    file = models.FileField(upload_to='class_resources/', blank=True, null=True)
    link = models.URLField(blank=True, null=True, max_length=500)
    uploaded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    
    TARGET_CHOICES = [
        ('all', 'All Users'),
        ('teachers', 'Teachers Only'),
        ('students', 'Students Only'),
    ]
    target_audience = models.CharField(max_length=20, choices=TARGET_CHOICES, default='all', help_text="Who can see this if not linked to a class?")
    
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
        
    class Meta:
        ordering = ['-uploaded_at']


class SchemeOfWork(models.Model):
    """Teacher-uploaded termly scheme of work screenshot. SchoolPadi uses the extracted topics to guide lessons."""
    TERM_CHOICES = (
        ('first', 'First Term'),
        ('second', 'Second Term'),
        ('third', 'Third Term'),
    )
    class_subject = models.ForeignKey(
        ClassSubject, on_delete=models.CASCADE, related_name='schemes_of_work'
    )
    academic_year = models.ForeignKey(
        AcademicYear, on_delete=models.CASCADE, related_name='schemes_of_work'
    )
    term = models.CharField(max_length=15, choices=TERM_CHOICES)
    image = models.ImageField(upload_to='schemes_of_work/', blank=True, null=True)
    # JSON list of topic strings extracted by GPT-4 Vision
    extracted_topics = models.TextField(blank=True, default='[]',
                                        help_text='JSON array of topic strings extracted from the image')
    # JSON dict mapping each topic string to its indicator code (e.g. {"Integers": "B8.2.1.1.1"})
    extracted_indicators = models.TextField(blank=True, default='{}',
                                            help_text='JSON dict mapping topic to indicator code')
    uploaded_by = models.ForeignKey(
        'teachers.Teacher', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='schemes_of_work'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-uploaded_at']
        unique_together = ['class_subject', 'term', 'academic_year']
        verbose_name = 'Scheme of Work'
        verbose_name_plural = 'Schemes of Work'

    def __str__(self):
        return f"{self.class_subject} — {self.get_term_display()} {self.academic_year}"

    def get_topics(self):
        """Return the extracted topics as a Python list."""
        import json
        try:
            topics = json.loads(self.extracted_topics)
            return topics if isinstance(topics, list) else []
        except Exception:
            return []

    def get_indicators(self):
        """Return extracted indicators as a Python dict {topic: indicator_code}."""
        import json
        try:
            data = json.loads(self.extracted_indicators)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def get_topic_items(self):
        """Return list of (topic, indicator) tuples for template iteration."""
        indicators = self.get_indicators()
        return [(t, indicators.get(t, '')) for t in self.get_topics()]


class AdmissionApplication(models.Model):
    """Visitor-submitted admission application. Reviewed by admin; not yet enrolled."""

    STATUS_CHOICES = [
        ('pending',   'Pending Review'),
        ('reviewing', 'Under Review'),
        ('accepted',  'Accepted'),
        ('rejected',  'Rejected'),
    ]

    # Student
    first_name     = models.CharField(max_length=100)
    last_name      = models.CharField(max_length=100)
    date_of_birth  = models.DateField()
    gender         = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female')])
    grade          = models.CharField(max_length=50)

    # Parent / Guardian
    parent_name    = models.CharField(max_length=150)
    relationship   = models.CharField(max_length=20, choices=[
        ('father', 'Father'), ('mother', 'Mother'), ('guardian', 'Guardian'),
    ])
    phone          = models.CharField(max_length=30)
    email          = models.EmailField()
    address        = models.TextField()

    # Extra
    previous_school = models.CharField(max_length=200, blank=True)
    comments        = models.TextField(blank=True)

    # Admin
    status          = models.CharField(max_length=12, choices=STATUS_CHOICES, default='pending')
    admin_notes     = models.TextField(blank=True)
    submitted_at    = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'Admission Application'
        verbose_name_plural = 'Admission Applications'

    def __str__(self):
        return f"{self.first_name} {self.last_name} — {self.grade} ({self.get_status_display()})"

    @property
    def student_name(self):
        return f"{self.first_name} {self.last_name}"


# Import AI Tutor/Copilot models
from .tutor_models import (
    TutorSession,
    TutorMessage,
    PracticeQuestionSet,
    CopilotConversation,
    CopilotMessage,
)

# Import Gamification models
from .gamification_models import (
    StudentXP,
    Achievement,
    StudentAchievement,
)

# Import Study Arena models
from .arena_models import (
    StudyGroupRoom,
    StudyGroupMessage,
)

# Import Digital Pulse models
from .pulse_models import (
    PulseSession,
    PulseResponse,
)
