from django.db import models
from django_tenants.models import TenantMixin, DomainMixin

class School(TenantMixin):
    name = models.CharField(max_length=100)
    created_on = models.DateField(auto_now_add=True)
    
    # New Comprehensive Fields
    SCHOOL_TYPES = (
        ('primary', 'Primary School (Class 1-6)'),
        ('jhs', 'Junior High School (JHS 1-3)'),
        ('shs', 'Senior High School'),
        ('basic', 'Basic School (Kindergarten - JHS 3)'),
        ('other', 'Other / Tertiary'),
    )
    school_type = models.CharField(max_length=20, choices=SCHOOL_TYPES, default='basic')
    address = models.TextField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=50, default="Ghana")
    
    on_trial = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Default true, schema will be automatically created and synced when it is saved
    auto_create_schema = True

    def __str__(self):
        return self.name

class Domain(DomainMixin):
    pass
