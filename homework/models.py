from django.db import models
from django.utils import timezone
from accounts.models import User

class Homework(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.CASCADE, related_name='assignments')
    subject = models.ForeignKey('academics.Subject', on_delete=models.SET_NULL, null=True, blank=True)
    target_class = models.ForeignKey('academics.Class', on_delete=models.CASCADE, related_name='assignments')
    due_date = models.DateField()
    attachment = models.FileField(upload_to='homework_attachments/', blank=True, null=True)
    allow_retry = models.BooleanField(default=False, help_text="Allow students to retry if they scored below 50%")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-due_date', '-created_at']
        verbose_name = "Homework"
        verbose_name_plural = "Homeworks"

    def __str__(self):
        return f"{self.title} - {self.target_class}"

class Question(models.Model):
    QUESTION_TYPES = (
        ('mcq', 'Multiple Choice'),
        ('short', 'Short Answer'),
        ('essay', 'Essay'),
    )
    DOK_CHOICES = (
        (1, 'DOK 1: Recall'),
        (2, 'DOK 2: Skills/Concepts'),
        (3, 'DOK 3: Strategic Thinking'),
        (4, 'DOK 4: Extended Thinking'),
    )

    homework = models.ForeignKey(Homework, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    points = models.IntegerField(default=1)
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPES, default='mcq')
    dok_level = models.PositiveSmallIntegerField(choices=DOK_CHOICES, default=1)
    correct_answer = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.text[:50]}..."

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)
    
    def __str__(self):
        return self.text

class Submission(models.Model):
    homework = models.ForeignKey(Homework, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='homework_submissions')
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_late = models.BooleanField(default=False)
    attempt_number = models.PositiveSmallIntegerField(default=1)

    class Meta:
        # Allow multiple attempts; unique on (homework, student, attempt_number)
        unique_together = ['homework', 'student', 'attempt_number']

    @property
    def is_best(self):
        """True if this is the highest-scoring attempt."""
        best = (
            Submission.objects.filter(homework=self.homework, student=self.student)
            .order_by('-score').first()
        )
        return best and best.pk == self.pk

class Answer(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choice = models.ForeignKey(Choice, on_delete=models.CASCADE, null=True, blank=True)
    is_correct = models.BooleanField(default=False)
    text_response = models.TextField(blank=True)
    ai_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ai_feedback = models.TextField(blank=True)


