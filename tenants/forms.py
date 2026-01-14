import re
from django import forms
from django.core.exceptions import ValidationError
from .models import School, Domain
from academics.models import SchoolInfo

class SchoolSignupForm(forms.Form):
    school_name = forms.CharField(label="School Name", max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Kings College'}))
    schema_name = forms.CharField(label="School ID (Subdomain)", max_length=50, help_text="No spaces. e.g. 'kings'", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'kings'}))
    email = forms.EmailField(label="Admin Email", widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'admin@kings.edu'}))
    
    SCHOOL_TYPES = (
        ('primary', 'Primary School (Class 1-6)'),
        ('jhs', 'Junior High School (JHS 1-3)'),
        ('shs', 'Senior High School'),
        ('basic', 'Basic School (Kindergarten - JHS 3)'),
        ('other', 'Other / Tertiary'),
    )
    school_type = forms.ChoiceField(choices=SCHOOL_TYPES, widget=forms.Select(attrs={'class': 'form-select'}))
    phone = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}))
    country = forms.CharField(initial="Ghana", widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    def clean_schema_name(self):
        data = self.cleaned_data['schema_name'].lower().strip()
        
        # Validation checks
        if not re.match(r'^[a-z0-9]+$', data):
            raise ValidationError("School ID must contain only lowercase letters and numbers (no spaces).")
            
        reserved = ['public', 'admin', 'static', 'media', 'accounts', 'school', 'login', 'signup', 'register']
        if data in reserved:
            raise ValidationError(f"'{data}' is a reserved system name.")
            
        if School.objects.filter(schema_name=data).exists():
            raise ValidationError(f"The School ID '{data}' is already taken.")
            
        return data


class SchoolSetupForm(forms.ModelForm):
    primary_color = forms.CharField(
        label="Primary Color",
        max_length=7,
        required=False,
        widget=forms.TextInput(attrs={
            'type': 'color',
            'class': 'form-control form-control-color',
            'value': '#026e56'
        }),
        help_text="Main brand color for your school"
    )
    
    class Meta:
        model = SchoolInfo
        fields = ['name', 'address', 'phone', 'email', 'motto', 'logo']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Kings College'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'P.O. Box 123, City'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+233 24 123 4567'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'info@school.edu'}),
            'motto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Excellence and Integrity'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
        }

