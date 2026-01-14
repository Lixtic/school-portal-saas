from django.db import models
from accounts.models import User

class AcademicYear(models.Model):
    name = models.CharField(max_length=20)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name
    
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
    
    def save(self, *args, **kwargs):
        if not self.pk and SchoolInfo.objects.exists():
            # If valid, just update the first one instead of creating new
            self.pk = SchoolInfo.objects.first().pk
        super().save(*args, **kwargs)

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
