from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from .models import Homework
from academics.models import Class, Subject, ClassSubject

class HomeworkForm(forms.ModelForm):
    due_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    class Meta:
        model = Homework
        fields = ['title', 'target_class', 'subject', 'due_date', 'description', 'attachment']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'target_class': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Publish Assignment', css_class='btn btn-primary'))
        
        if teacher:
            # Filter classes and subjects based on what teacher teaches
            class_subjects = ClassSubject.objects.filter(teacher=teacher).select_related('class_name', 'subject')
            class_ids = set(cs.class_name.id for cs in class_subjects)
            subject_ids = set(cs.subject.id for cs in class_subjects)
            
            self.fields['target_class'].queryset = Class.objects.filter(id__in=class_ids)
            self.fields['subject'].queryset = Subject.objects.filter(id__in=subject_ids)
