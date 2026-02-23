# teachers/models.py
from django.db import models
from accounts.models import User

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=20, unique=True)
    date_of_birth = models.DateField()
    date_of_joining = models.DateField()
    qualification = models.CharField(max_length=200)
    subjects = models.ManyToManyField('academics.Subject', blank=True)
    
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
    topic = models.CharField(max_length=200)
    objectives = models.TextField(help_text="Specific learning outcomes")
    teaching_materials = models.TextField(blank=True, help_text="Materials needed for the lesson")
    
    # Lesson Procedure
    introduction = models.TextField(blank=True)
    presentation = models.TextField(blank=True, help_text="Main teaching activity")
    evaluation = models.TextField(blank=True, help_text="How students will be assessed")
    homework = models.TextField(blank=True)
    
    date_added = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-week_number', '-date_added']
    
    def __str__(self):
        return f"Week {self.week_number}: {self.subject} - {self.topic}"
