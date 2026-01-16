"""
Subscription and billing models for multi-tenant SaaS
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal


class SubscriptionPlan(models.Model):
    """Base subscription plans (Basic, Pro, Enterprise)"""
    PLAN_TYPES = [
        ('trial', 'Trial'),
        ('basic', 'Basic'),
        ('pro', 'Professional'),
        ('enterprise', 'Enterprise'),
    ]
    
    BILLING_CYCLES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annual', 'Annual'),
    ]
    
    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, unique=True)
    description = models.TextField()
    
    # Pricing
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quarterly_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    annual_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Limits
    max_students = models.IntegerField(default=100, help_text="Maximum students allowed")
    max_teachers = models.IntegerField(default=20, help_text="Maximum teachers allowed")
    max_storage_gb = models.IntegerField(default=10, help_text="Storage limit in GB")
    
    # Features
    custom_domain = models.BooleanField(default=False)
    white_label = models.BooleanField(default=False)
    priority_support = models.BooleanField(default=False)
    api_access = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['monthly_price']
    
    def __str__(self):
        return f"{self.name} (${self.monthly_price}/mo)"
    
    def get_price_for_cycle(self, cycle):
        """Get price for specific billing cycle"""
        prices = {
            'monthly': self.monthly_price,
            'quarterly': self.quarterly_price,
            'annual': self.annual_price,
        }
        return prices.get(cycle, self.monthly_price)


class AddOn(models.Model):
    """Modular add-ons schools can purchase"""
    CATEGORY_CHOICES = [
        ('ai', 'AI & Automation'),
        ('analytics', 'Analytics & Reporting'),
        ('communication', 'Communication'),
        ('integration', 'Integrations'),
        ('storage', 'Storage & Resources'),
        ('feature', 'Premium Features'),
    ]
    
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='bi-plus-circle', help_text="Bootstrap icon class")
    
    # Pricing
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_one_time = models.BooleanField(default=False, help_text="One-time purchase vs recurring")
    
    # Availability
    is_active = models.BooleanField(default=True)
    available_for_plans = models.JSONField(
        default=list,
        help_text="List of plan_types that can purchase this add-on"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['category', 'monthly_price']
    
    def __str__(self):
        return f"{self.name} (${self.monthly_price}/mo)"


class SchoolSubscription(models.Model):
    """Active subscription for a school tenant"""
    STATUS_CHOICES = [
        ('trial', 'Trial'),
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('cancelled', 'Cancelled'),
        ('suspended', 'Suspended'),
    ]
    
    school = models.OneToOneField('tenants.School', on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    billing_cycle = models.CharField(max_length=20, choices=SubscriptionPlan.BILLING_CYCLES, default='monthly')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trial')
    
    # Dates
    started_at = models.DateTimeField(default=timezone.now)
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    current_period_start = models.DateTimeField(default=timezone.now)
    current_period_end = models.DateTimeField()
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # Billing
    mrr = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Monthly Recurring Revenue")
    
    # Usage tracking
    current_students = models.IntegerField(default=0)
    current_teachers = models.IntegerField(default=0)
    current_storage_gb = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    auto_renew = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.school.name} - {self.plan.name} ({self.status})"
    
    def is_trial(self):
        return self.status == 'trial' and self.trial_ends_at and timezone.now() < self.trial_ends_at
    
    def is_active_paid(self):
        return self.status == 'active' and not self.is_trial()
    
    def days_until_renewal(self):
        if self.current_period_end:
            delta = self.current_period_end - timezone.now()
            return max(0, delta.days)
        return 0
    
    def calculate_mrr(self):
        """Calculate MRR based on plan and add-ons"""
        # Base plan MRR
        if self.billing_cycle == 'monthly':
            base_mrr = self.plan.monthly_price
        elif self.billing_cycle == 'quarterly':
            base_mrr = self.plan.quarterly_price / 3
        elif self.billing_cycle == 'annual':
            base_mrr = self.plan.annual_price / 12
        else:
            base_mrr = self.plan.monthly_price
        
        # Add-ons MRR
        addons_mrr = sum(
            addon.addon.monthly_price 
            for addon in self.active_addons.filter(is_active=True)
            if not addon.addon.is_one_time
        )
        
        total_mrr = base_mrr + addons_mrr
        self.mrr = total_mrr
        self.save(update_fields=['mrr'])
        return total_mrr


class SchoolAddOn(models.Model):
    """Add-ons purchased by a school"""
    subscription = models.ForeignKey(SchoolSubscription, on_delete=models.CASCADE, related_name='active_addons')
    addon = models.ForeignKey(AddOn, on_delete=models.PROTECT)
    
    is_active = models.BooleanField(default=True)
    purchased_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['subscription', 'addon']
        ordering = ['-purchased_at']
    
    def __str__(self):
        return f"{self.subscription.school.name} - {self.addon.name}"


class Invoice(models.Model):
    """Billing invoices"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    subscription = models.ForeignKey(SchoolSubscription, on_delete=models.CASCADE, related_name='invoices')
    invoice_number = models.CharField(max_length=50, unique=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Amounts
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Dates
    issued_at = models.DateTimeField(default=timezone.now)
    due_at = models.DateTimeField()
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # Items (JSON)
    line_items = models.JSONField(default=list, help_text="List of invoice items")
    
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-issued_at']
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.subscription.school.name}"
    
    def mark_paid(self):
        self.status = 'paid'
        self.paid_at = timezone.now()
        self.save()


class ChurnEvent(models.Model):
    """Track subscription cancellations for churn analysis"""
    REASON_CHOICES = [
        ('price', 'Too Expensive'),
        ('features', 'Missing Features'),
        ('support', 'Poor Support'),
        ('competitor', 'Switched to Competitor'),
        ('closure', 'School Closed'),
        ('other', 'Other'),
    ]
    
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='churn_events')
    subscription = models.ForeignKey(SchoolSubscription, on_delete=models.SET_NULL, null=True)
    
    cancelled_at = models.DateTimeField(default=timezone.now)
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    reason_detail = models.TextField(blank=True)
    
    # Metrics
    lifetime_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    months_subscribed = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-cancelled_at']
    
    def __str__(self):
        return f"Churn: {self.school.name} on {self.cancelled_at.date()}"
