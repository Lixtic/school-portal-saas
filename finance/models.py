import secrets
import string

from django.db import models
from django.db.models import UniqueConstraint, Q
from students.models import Student
from academics.models import Class, AcademicYear
from accounts.models import User
from django.utils import timezone


def generate_payment_reference():
    """Generate a unique payment reference like RCP-20260319-A7X2."""
    date_part = timezone.now().strftime('%Y%m%d')
    chars = string.ascii_uppercase + string.digits
    for _ in range(10):
        suffix = ''.join(secrets.choice(chars) for _ in range(4))
        ref = f'RCP-{date_part}-{suffix}'
        from finance.models import Payment
        if not Payment.objects.filter(reference=ref).exists():
            return ref
    # Fallback with longer suffix
    suffix = ''.join(secrets.choice(chars) for _ in range(8))
    return f'RCP-{date_part}-{suffix}'

TERM_CHOICES = (
    ('first', 'First Term'),
    ('second', 'Second Term'),
    ('third', 'Third Term'),
)

class FeeHead(models.Model):
    """
    Examples: Tuition, Library Fee, Uniform, Bus Fee
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class FeeStructure(models.Model):
    """
    Defines the standard fee for a class for a specific term/year.
    """
    head = models.ForeignKey(FeeHead, on_delete=models.CASCADE)
    class_level = models.ForeignKey(Class, on_delete=models.CASCADE, verbose_name="Class")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    term = models.CharField(max_length=20, choices=TERM_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField(null=True, blank=True)
    assigned_collector = models.ForeignKey(
        'teachers.Teacher',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='fee_collection_tasks',
        verbose_name="Assigned Collector",
        help_text="Teacher responsible for collecting this fee",
    )

    class Meta:
        unique_together = ('head', 'class_level', 'academic_year', 'term')

    def __str__(self):
        return f"{self.head.name} - {self.class_level} ({self.amount})"

class StudentFee(models.Model):
    """
    An assigned fee to a specific student.
    Created automatically when 'Bulk Assign' is used or manually for specific fees.
    """
    STATUS_CHOICES = (
        ('unpaid', 'Unpaid'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
    )

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fees')
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE)
    amount_payable = models.DecimalField(max_digits=10, decimal_places=2, help_text="Can be adjusted for scholarships")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unpaid')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'fee_structure')

    def __str__(self):
        return f"{self.student} - {self.fee_structure.head.name}"

    @property
    def total_paid(self):
        return sum(payment.amount for payment in self.payments.all())

    @property
    def balance(self):
        return self.amount_payable - self.total_paid

    def update_status(self):
        from django.db.models import Sum
        from decimal import Decimal
        paid = self.payments.aggregate(total=Sum('amount'))['total'] or Decimal('0')
        if paid >= self.amount_payable:
            self.status = 'paid'
        elif paid > 0:
            self.status = 'partial'
        else:
            self.status = 'unpaid'
        self.save(update_fields=['status'])

class Payment(models.Model):
    """
    A transaction record against a specific StudentFee.
    """
    student_fee = models.ForeignKey(StudentFee, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
    reference = models.CharField(max_length=100, blank=True, default='', help_text="Receipt number or Transaction ID")
    method = models.CharField(max_length=50, default='Cash', choices=[('Cash', 'Cash'), ('Bank Transfer', 'Bank Transfer'), ('POS', 'POS')])
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['reference'],
                name='unique_non_empty_reference',
                condition=~Q(reference=''),
            ),
        ]

    def __str__(self):
        return f"{self.amount} - {self.date}"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = generate_payment_reference()
        super().save(*args, **kwargs)
        self.student_fee.update_status()
