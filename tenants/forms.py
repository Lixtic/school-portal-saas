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
    address = forms.CharField(label="School Address", required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'P.O. Box 123, Accra'}))
    phone = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}))
    country = forms.CharField(initial="Ghana", widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    # Contact Person (Onboarding)
    contact_person_name = forms.CharField(label="Contact Person Name", max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'John Doe'}))
    contact_person_title = forms.CharField(label="Title/Position", max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Principal / Headmaster'}))
    contact_person_email = forms.EmailField(label="Contact Email", widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'john.doe@school.edu'}))
    contact_person_phone = forms.CharField(label="Contact Phone", max_length=20, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+233 XX XXX XXXX'}))
    
    # Verification Documents
    registration_certificate = forms.FileField(
        label="School Registration Certificate",
        required=True,
        help_text="Upload official registration/license document (PDF, JPG, PNG)",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'})
    )
    tax_id_document = forms.FileField(
        label="Tax Identification Document",
        required=False,
        help_text="Tax ID or business registration (optional)",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'})
    )
    additional_documents = forms.FileField(
        label="Additional Documents",
        required=False,
        help_text="Any other verification documents (optional)",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'})
    )
    
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
    
    def clean_registration_certificate(self):
        file = self.cleaned_data.get('registration_certificate')
        if file:
            if file.size > 10 * 1024 * 1024:  # 10MB limit
                raise ValidationError("File size must be under 10MB")
            allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
            import os
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in allowed_extensions:
                raise ValidationError(f"Only PDF and image files are allowed")
        return file


class SchoolApprovalForm(forms.ModelForm):
    """Form for system admins to approve/reject schools"""
    class Meta:
        model = School
        fields = ['approval_status', 'admin_notes', 'rejection_reason', 'is_active', 'on_trial']
        widgets = {
            'approval_status': forms.Select(attrs={'class': 'form-select'}),
            'admin_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Internal notes about this review...'}),
            'rejection_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Provide reason if rejecting...'}),
        }


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

