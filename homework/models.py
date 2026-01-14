from django.db import models
from accounts.models import User

class Homework(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.CASCADE, related_name='assignments')
    subject = models.ForeignKey('academics.Subject', on_delete=models.CASCADE)
    target_class = models.ForeignKey('academics.Class', on_delete=models.CASCADE, related_name='assignments')
    due_date = models.DateField()
    attachment = models.FileField(upload_to='homework_attachments/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-due_date', '-created_at']
        verbose_name = "Homework"
        verbose_name_plural = "Homeworks"

    def __str__(self):
        return f"{self.title} - {self.target_class}"

