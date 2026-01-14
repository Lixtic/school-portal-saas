from django.db import models
from django.conf import settings
from django.utils import timezone

class Vendor(models.Model):
    name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    service_type = models.CharField(max_length=100, help_text="e.g. Stationery, Catering, Maintenance")
    
    def __str__(self):
        return self.name

class ExpenseCategory(models.Model):
    name = models.CharField(max_length=50) # Salaries, Utilities, Repair, Supplies
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "Expense Categories"
        
    def __str__(self):
        return self.name

class Expense(models.Model):
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT)
    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True)
    receipt_file = models.FileField(upload_to='expenses/%Y/%m/', blank=True, null=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.amount}"

class Asset(models.Model):
    CONDITION_CHOICES = (
        ('new', 'New'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('broken', 'Broken/Repair Needed'),
    )
    
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True, help_text="Asset Tag/ID")
    category = models.CharField(max_length=50) # Electronics, Furniture, Vehicle
    purchase_date = models.DateField(null=True, blank=True)
    purchase_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currrent_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    location = models.CharField(max_length=100) # Library, Lab 1, Staff Room
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    assigned_to = models.CharField(max_length=100, blank=True, help_text="Staff member responsible")
    
    def __str__(self):
        return f"{self.name} ({self.code})"
