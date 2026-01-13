from django import forms
from .models import SchoolInfo, GalleryImage, Resource

class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ['title', 'description', 'file', 'link', 'resource_type', 'curriculum', 'target_audience', 'class_subject']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'resource_type': forms.Select(attrs={'class': 'form-select'}),
            'curriculum': forms.Select(attrs={'class': 'form-select'}),
            'target_audience': forms.Select(attrs={'class': 'form-select'}),
            'class_subject': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['class_subject'].required = False
        self.fields['class_subject'].help_text = "Optional: Leave blank for general resources"
        self.fields['curriculum'].initial = 'ges_jhs_new'

class GalleryImageForm(forms.ModelForm):
    class Meta:
        model = GalleryImage
        fields = ['title', 'caption', 'image', 'category']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'caption': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }

class SchoolInfoForm(forms.ModelForm):
    class Meta:
        model = SchoolInfo
        fields = ['name', 'address', 'phone', 'email', 'motto', 'logo', 'primary_color', 'secondary_color']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'motto': forms.TextInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'primary_color': forms.TextInput(attrs={'class': 'form-control form-control-color', 'type': 'color', 'title': 'Choose Main Color'}),
            'secondary_color': forms.TextInput(attrs={'class': 'form-control form-control-color', 'type': 'color', 'title': 'Choose Sidebar Color'}),
        }
