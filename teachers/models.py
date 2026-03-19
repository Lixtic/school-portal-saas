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
