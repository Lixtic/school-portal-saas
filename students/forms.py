from datetime import date
import random
import string
from django import forms
from django.utils.text import slugify
from accounts.models import User
from academics.models import Class
from .models import Student


class StudentQuickAddForm(forms.Form):
    first_name = forms.CharField(max_length=150, label="First name", widget=forms.TextInput(attrs={'class': 'vTextField'}))
    last_name = forms.CharField(max_length=150, label="Last name", widget=forms.TextInput(attrs={'class': 'vTextField'}))
    age = forms.IntegerField(min_value=3, max_value=25, label="Age", widget=forms.NumberInput(attrs={'class': 'vIntegerField'}))
    current_class = forms.ModelChoiceField(queryset=Class.objects.all(), label="Class", widget=forms.Select(attrs={'class': 'vForeignKeyRawIdAdminField'}))

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)

    def save_m2m(self):
        pass

    def _generate_username(self, base):
        base_slug = slugify(base).replace('-', '') or 'student'
        candidate = base_slug
        while User.objects.filter(username=candidate).exists():
            candidate = f"{base_slug}{random.randint(1000, 9999)}"
        return candidate

    def _generate_admission_number(self):
        prefix = 'ADM'
        while True:
            suffix = ''.join(random.choices(string.digits, k=4))
            adm_no = f"{prefix}{suffix}"
            if not Student.objects.filter(admission_number=adm_no).exists():
                return adm_no

    def save(self, commit=True):
        first_name = self.cleaned_data['first_name'].strip()
        last_name = self.cleaned_data['last_name'].strip()
        age = self.cleaned_data['age']
        current_class = self.cleaned_data['current_class']

        username = self._generate_username(f"{first_name}.{last_name}")
        email = f"{username}@school.local"
        user = User(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            user_type='student',
        )
        user.set_unusable_password()
        # Always save user to generate PK
        user.save()

        dob_year = max(1900, date.today().year - age)
        date_of_birth = date(dob_year, 1, 1)

        admission_number = self._generate_admission_number()

        student = Student(
            user=user,
            admission_number=admission_number,
            date_of_birth=date_of_birth,
            gender='male',
            date_of_admission=date.today(),
            current_class=current_class,
            roll_number='',
            blood_group='',
            emergency_contact='N/A',
        )

        # Always save student
        student.save()
        self.instance = student
        return student

    def save_m2m(self):
        # No many-to-many fields in quick add form, so this is a no-op
        pass

class StudentForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = Student
        fields = ['admission_number', 'date_of_birth', 'gender', 'date_of_admission', 
                  'current_class', 'roll_number', 'blood_group', 'emergency_contact']
        widgets = {
            'admission_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Auto-generated if blank'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'date_of_admission': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'current_class': forms.Select(attrs={'class': 'form-select'}),
            'roll_number': forms.TextInput(attrs={'class': 'form-control'}),
            'blood_group': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['admission_number'].required = False
        self.fields['date_of_admission'].initial = date.today()
        self.fields['roll_number'].required = False
        self.fields['blood_group'].required = False
        self.fields['emergency_contact'].required = False

