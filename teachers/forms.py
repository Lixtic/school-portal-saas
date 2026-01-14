from django import forms
from datetime import date
import random
import string
from django.utils.text import slugify
from accounts.models import User
from academics.models import Resource
# from parents.models import Homework  <-- Removed
from .models import Teacher

# HomeworkForm Removed - Moved to homework app

class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ['title', 'description', 'file', 'link', 'resource_type', 'curriculum']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'resource_type': forms.Select(attrs={'class': 'form-select'}),
            'curriculum': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['curriculum'].initial = 'ges_jhs_new'


class TeacherQuickAddForm(forms.Form):
    first_name = forms.CharField(max_length=150, label="First name", widget=forms.TextInput(attrs={'class': 'vTextField'}))
    last_name = forms.CharField(max_length=150, label="Last name", widget=forms.TextInput(attrs={'class': 'vTextField'}))
    age = forms.IntegerField(min_value=18, max_value=70, label="Age", widget=forms.NumberInput(attrs={'class': 'vIntegerField'}))

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)

    def save_m2m(self):
        pass

    def _generate_username(self, base):
        base_slug = slugify(base).replace('-', '') or 'teacher'
        candidate = base_slug
        while User.objects.filter(username=candidate).exists():
            candidate = f"{base_slug}{random.randint(1000, 9999)}"
        return candidate

    def _generate_employee_id(self):
        prefix = 'TCHR'
        while True:
            suffix = ''.join(random.choices(string.digits, k=4))
            emp_id = f"{prefix}{suffix}"
            if not Teacher.objects.filter(employee_id=emp_id).exists():
                return emp_id

    def save(self, commit=True):
        first_name = self.cleaned_data['first_name'].strip()
        last_name = self.cleaned_data['last_name'].strip()
        age = self.cleaned_data['age']

        username = self._generate_username(f"{first_name}.{last_name}")
        email = f"{username}@school.local"
        user = User(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            user_type='teacher',
        )
        user.set_unusable_password()
        # Always save user
        user.save()

        dob_year = max(1900, date.today().year - age)
        date_of_birth = date(dob_year, 1, 1)
        employee_id = self._generate_employee_id()

        teacher = Teacher(
            user=user,
            employee_id=employee_id,
            date_of_birth=date_of_birth,
            date_of_joining=date.today(),
            qualification='Not provided',
        )

        # Always save teacher
        teacher.save()
        self.instance = teacher
        return teacher

    def save_m2m(self):
        # No many-to-many fields in quick add form, so this is a no-op
        pass

from .models import LessonPlan
from academics.models import Subject, Class

class LessonPlanForm(forms.ModelForm):
    class Meta:
        model = LessonPlan
        fields = [
            'week_number', 'subject', 'school_class', 'topic', 
            'objectives', 'teaching_materials', 
            'introduction', 'presentation', 'evaluation', 'homework'
        ]
        widgets = {
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'school_class': forms.Select(attrs={'class': 'form-select'}),
            'week_number': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 52}),
            'topic': forms.TextInput(attrs={'class': 'form-control'}),
            'objectives': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'teaching_materials': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'introduction': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'presentation': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'evaluation': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'homework': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        self.teacher = kwargs.pop('teacher', None)
        super(LessonPlanForm, self).__init__(*args, **kwargs)
        if self.teacher:
            # Filter subjects if teacher assign to subjects
            if self.teacher.subjects.exists():
                self.fields['subject'].queryset = self.teacher.subjects.all()

class TeacherCreateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = Teacher
        fields = ['employee_id', 'date_of_birth', 'date_of_joining', 'qualification', 'subjects']
        widgets = {
            'employee_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Auto-generated if blank'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_of_joining': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control'}),
            'subjects': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee_id'].required = False
        self.fields['date_of_joining'].initial = date.today()
        self.fields['qualification'].required = False

class TeacherEditForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = Teacher
        fields = ['employee_id', 'date_of_birth', 'date_of_joining', 'qualification', 'subjects']
        widgets = {
            'employee_id': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_of_joining': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control'}),
            'subjects': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Pre-populate user fields
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
            if hasattr(self.instance.user, 'profile'):
                self.fields['phone'].initial = self.instance.user.profile.phone
        self.fields['employee_id'].widget.attrs['readonly'] = True

    def save(self, commit=True):
        teacher = super().save(commit=False)
        
        # Update user fields
        teacher.user.first_name = self.cleaned_data['first_name']
        teacher.user.last_name = self.cleaned_data['last_name']
        teacher.user.email = self.cleaned_data['email']
        
        if commit:
            teacher.user.save()
            teacher.save()
            self.save_m2m()
        
        return teacher
