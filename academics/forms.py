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
        fields = [
            'name', 'address', 'phone', 'email', 'motto', 'logo', 
            'primary_color', 'secondary_color', 'homepage_template',
            'hero_title', 'hero_subtitle', 'cta_primary_text', 'cta_primary_url',
            'cta_secondary_text', 'cta_secondary_url',
            'stat1_number', 'stat1_label', 'stat2_number', 'stat2_label',
            'stat3_number', 'stat3_label', 'stat4_number', 'stat4_label',
            'feature1_title', 'feature1_description', 'feature1_icon',
            'feature2_title', 'feature2_description', 'feature2_icon',
            'feature3_title', 'feature3_description', 'feature3_icon',
            'about_title', 'about_description',
            'facebook_url', 'twitter_url', 'instagram_url', 'linkedin_url', 'youtube_url',
            'show_stats_section', 'show_programs_section', 'show_gallery_preview'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'motto': forms.TextInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'primary_color': forms.TextInput(attrs={'class': 'form-control form-control-color', 'type': 'color', 'title': 'Choose Main Color'}),
            'secondary_color': forms.TextInput(attrs={'class': 'form-control form-control-color', 'type': 'color', 'title': 'Choose Sidebar Color'}),
            'homepage_template': forms.Select(attrs={'class': 'form-select'}),
            'hero_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Leave empty to use school name'}),
            'hero_subtitle': forms.TextInput(attrs={'class': 'form-control'}),
            'cta_primary_text': forms.TextInput(attrs={'class': 'form-control'}),
            'cta_primary_url': forms.TextInput(attrs={'class': 'form-control'}),
            'cta_secondary_text': forms.TextInput(attrs={'class': 'form-control'}),
            'cta_secondary_url': forms.TextInput(attrs={'class': 'form-control'}),
            'stat1_number': forms.TextInput(attrs={'class': 'form-control'}),
            'stat1_label': forms.TextInput(attrs={'class': 'form-control'}),
            'stat2_number': forms.TextInput(attrs={'class': 'form-control'}),
            'stat2_label': forms.TextInput(attrs={'class': 'form-control'}),
            'stat3_number': forms.TextInput(attrs={'class': 'form-control'}),
            'stat3_label': forms.TextInput(attrs={'class': 'form-control'}),
            'stat4_number': forms.TextInput(attrs={'class': 'form-control'}),
            'stat4_label': forms.TextInput(attrs={'class': 'form-control'}),
            'feature1_title': forms.TextInput(attrs={'class': 'form-control'}),
            'feature1_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'feature1_icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'fa-award'}),
            'feature2_title': forms.TextInput(attrs={'class': 'form-control'}),
            'feature2_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'feature2_icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'fa-users'}),
            'feature3_title': forms.TextInput(attrs={'class': 'form-control'}),
            'feature3_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'feature3_icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'fa-building'}),
            'about_title': forms.TextInput(attrs={'class': 'form-control'}),
            'about_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'facebook_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://facebook.com/yourschool'}),
            'twitter_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://twitter.com/yourschool'}),
            'instagram_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://instagram.com/yourschool'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://linkedin.com/company/yourschool'}),
            'youtube_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://youtube.com/c/yourschool'}),
        }
