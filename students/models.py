from django.db import models
from accounts.models import User
from decimal import Decimal, InvalidOperation

class Student(models.Model):
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    admission_number = models.CharField(max_length=20, unique=True)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='male')
    date_of_admission = models.DateField()
    current_class = models.ForeignKey('academics.Class', on_delete=models.SET_NULL, null=True)
    roll_number = models.CharField(max_length=10, blank=True)
    blood_group = models.CharField(max_length=5, blank=True)
    emergency_contact = models.CharField(max_length=15)
    region = models.CharField(max_length=100, blank=True, default='')
    city = models.CharField(max_length=100, blank=True, default='')
    curriculum = models.CharField(max_length=150, blank=True, default='')
    interests = models.JSONField(default=list, blank=True)

    LANGUAGE_CHOICES = (
        ('english', 'English'),
        ('twi', 'Twi / Akan'),
        ('hausa', 'Hausa'),
        ('ewe', 'Ewe'),
        ('ga', 'Ga'),
        ('dagbani', 'Dagbani'),
        ('french', 'French'),
        ('other', 'Other'),
    )
    preferred_language = models.CharField(
        max_length=20, choices=LANGUAGE_CHOICES, default='english', blank=True,
        help_text="Student's primary spoken language (informs Aura's vocabulary style)"
    )
    aura_notes = models.TextField(
        blank=True, default='',
        help_text="Teacher/admin notes for Aura — e.g. 'struggles with fractions', 'preparing for BECE', 'gifted in science'"
    )
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.admission_number})"


class Attendance(models.Model):
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
    )
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    remarks = models.TextField(blank=True)
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"{self.student} - {self.date} - {self.status}"
    
    class Meta:
        unique_together = ['student', 'date']
        ordering = ['-date']


class Grade(models.Model):
    # Fixed TERM_CHOICES - using consistent values with display names
    TERM_CHOICES = (
        ('first', 'First Term'),
        ('second', 'Second Term'),
        ('third', 'Third Term'),
    )
    
    GRADE_CHOICES = (
        ('1', 'Highest'),
        ('2', 'Higher'),
        ('3', 'High'),
        ('4', 'High Average'),
        ('5', 'Average'),
        ('6', 'Low Average'),
        ('7', 'Low'),
        ('8', 'Lower'),
        ('9', 'Lowest'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey('academics.Subject', on_delete=models.CASCADE)
    academic_year = models.ForeignKey('academics.AcademicYear', on_delete=models.CASCADE)
    exam_type = models.ForeignKey('students.ExamType', on_delete=models.SET_NULL, null=True, blank=True)
    
    # FIXED: Proper CharField with choices and reduced max_length
    term = models.CharField(
        max_length=10, 
        choices=TERM_CHOICES, 
        default='first'
    )
    
    # Class work (30%)
    class_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Exams (70%)
    exams_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Auto-calculated fields
    total_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    grade = models.CharField(max_length=2, choices=GRADE_CHOICES, blank=True)
    remarks = models.CharField(max_length=50, blank=True)
    
    # Ranking
    subject_position = models.IntegerField(default=0, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Convert scores to Decimal if they are strings or other types
        try:
            self.class_score = Decimal(str(self.class_score).strip())
            self.exams_score = Decimal(str(self.exams_score).strip())
        except (ValueError, InvalidOperation):
            # Handle invalid score values
            self.class_score = Decimal('0.00')
            self.exams_score = Decimal('0.00')
        
        # Calculate total (class_score + exams_score)
        self.total_score = self.class_score + self.exams_score
        
        # Ensure total_score doesn't exceed 100
        if self.total_score > Decimal('100'):
            self.total_score = Decimal('100.00')
        
        # Determine grade based on total score
        # Use per-tenant GradingScale if configured, else Ghana default
        graded = False
        try:
            from academics.models import GradingScale
            scale = GradingScale.objects.all()  # ordered by -min_score
            if scale.exists():
                for row in scale:
                    if self.total_score >= row.min_score:
                        self.grade = row.grade_label
                        self.remarks = row.remarks
                        graded = True
                        break
                if not graded:
                    last = scale.last()
                    self.grade = last.grade_label
                    self.remarks = last.remarks
                    graded = True
        except Exception:
            pass

        if not graded:
            # Fallback: Ghana grading system (hardcoded default)
            if self.total_score >= Decimal('80'):
                self.grade = '1'
                self.remarks = 'Highest'
            elif self.total_score >= Decimal('70'):
                self.grade = '2'
                self.remarks = 'Higher'
            elif self.total_score >= Decimal('65'):
                self.grade = '3'
                self.remarks = 'High'
            elif self.total_score >= Decimal('60'):
                self.grade = '4'
                self.remarks = 'High Average'
            elif self.total_score >= Decimal('55'):
                self.grade = '5'
                self.remarks = 'Average'
            elif self.total_score >= Decimal('50'):
                self.grade = '6'
                self.remarks = 'Low Average'
            elif self.total_score >= Decimal('45'):
                self.grade = '7'
                self.remarks = 'Low'
            elif self.total_score >= Decimal('40'):
                self.grade = '8'
                self.remarks = 'Lower'
            else:
                self.grade = '9'
                self.remarks = 'Lowest'
        
        super().save(*args, **kwargs)
        
        # After saving, update rankings for this subject
        self.update_subject_rankings()
    
    def update_subject_rankings(self):
        """Update rankings for all students in the same class for this subject"""
        if not self.student.current_class:
            return  # Skip if student has no current class
            
        # Get all grades for this subject in the same class, academic year, and term
        grades_in_subject = Grade.objects.filter(
            subject=self.subject,
            academic_year=self.academic_year,
            term=self.term,
            student__current_class=self.student.current_class
        ).exclude(total_score__isnull=True).order_by('-total_score')
        
        # Assign positions (handle ties by giving same position to equal scores)
        previous_score = None
        position = 0
        
        for grade in grades_in_subject:
            # Convert to Decimal for safe comparison
            current_score = Decimal(str(grade.total_score))
            if current_score != previous_score:
                position += 1
                previous_score = current_score
            Grade.objects.filter(id=grade.id).update(subject_position=position)
    
    def get_term_display(self):
        """Returns the human-readable term name"""
        return dict(self.TERM_CHOICES).get(self.term, self.term)
    
    def percentage(self):
        """Returns total score as percentage"""
        return float(self.total_score)
    
    def is_first_term(self):
        """Check if this is first term"""
        return self.term == 'first'
    
    def is_second_term(self):
        """Check if this is second term"""
        return self.term == 'second'
    
    def is_third_term(self):
        """Check if this is third term"""
        return self.term == 'third'
    
    def __str__(self):
        term_display = self.get_term_display()
        exam_label = f" - {self.exam_type.name}" if self.exam_type else ''
        return f"{self.student} - {self.subject}{exam_label} - {term_display} ({self.academic_year})"
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['student', 'subject', 'academic_year', 'term', 'exam_type']
        indexes = [
            models.Index(fields=['student', 'term'], name='grade_student_term_idx'),
            models.Index(fields=['student', 'academic_year', 'term'], name='grade_student_year_term_idx'),
        ]


class ExamType(models.Model):
    """Tenant-configurable exam/assessment category."""

    name = models.CharField(max_length=80, unique=True)
    description = models.TextField(blank=True)
    weight_percent = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        status = 'active' if self.is_active else 'inactive'
        return f"{self.name} ({status})"

class ClassExercise(models.Model):
    class_subject = models.ForeignKey('academics.ClassSubject', on_delete=models.CASCADE)
    term = models.CharField(max_length=10, choices=Grade.TERM_CHOICES, default='first')
    title = models.CharField(max_length=100)
    max_marks = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    date_assigned = models.DateField(auto_now_add=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.title} - {self.class_subject}"

class StudentExerciseScore(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    exercise = models.ForeignKey(ClassExercise, on_delete=models.CASCADE, related_name='scores')
    score = models.DecimalField(max_digits=5, decimal_places=2)
    remarks = models.CharField(max_length=100, blank=True)

    class Meta:
        unique_together = ['student', 'exercise']
