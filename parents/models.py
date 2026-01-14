# parents/models.py
from django.db import models
from accounts.models import User

class Parent(models.Model):
    RELATION_CHOICES = (
        ('father', 'Father'),
        ('mother', 'Mother'),
        ('guardian', 'Guardian'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    relation = models.CharField(max_length=10, choices=RELATION_CHOICES)
    occupation = models.CharField(max_length=100, blank=True)
    children = models.ManyToManyField('students.Student', related_name='parents')
    

    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.get_relation_display()})"
