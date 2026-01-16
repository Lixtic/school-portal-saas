"""
Track AI Tutor usage and sessions
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone


class TutorSession(models.Model):
    """Track AI tutor chat sessions"""
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='tutor_sessions')
    subject = models.ForeignKey('academics.Subject', on_delete=models.SET_NULL, null=True, blank=True)
    
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    message_count = models.IntegerField(default=0)
    topics_discussed = models.JSONField(default=list, blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.started_at.date()}"


class TutorMessage(models.Model):
    """Individual messages in tutor sessions"""
    session = models.ForeignKey(TutorSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=[('user', 'Student'), ('assistant', 'AI Tutor')])
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}"


class PracticeQuestionSet(models.Model):
    """Generated practice question sets"""
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='practice_sets')
    subject = models.ForeignKey('academics.Subject', on_delete=models.CASCADE)
    topic = models.CharField(max_length=200)
    difficulty = models.CharField(
        max_length=20, 
        choices=[('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')],
        default='medium'
    )
    
    questions = models.JSONField(help_text="AI-generated questions and answers")
    
    generated_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.IntegerField(null=True, blank=True, help_text="Percentage score")
    
    class Meta:
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.subject.name}: {self.topic}"
