from django import forms
from .models import SMSMessage, EmailCampaign
from academics.models import Class

class SMSForm(forms.ModelForm):
    recipient_type = forms.ChoiceField(choices=[
        ('class', 'Specific Class Parents'),
        ('teachers', 'All Teachers'),
        ('staff', 'All Staff'),
        ('individual', 'Individual Number')
    ], widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_recipient_type'}))
    
    target_class = forms.ModelChoiceField(
        queryset=Class.objects.all(), 
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_target_class'})
    )
    
    class Meta:
        model = SMSMessage
        fields = ['recipient_number', 'message_body']
        widgets = {
            'recipient_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Only if Individual type selected'}),
            'message_body': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
        labels = {
            'message_body': 'Message Content',
            'recipient_number': 'Phone Number'
        }

class EmailForm(forms.ModelForm):
    class Meta:
        model = EmailCampaign
        fields = ['subject', 'recipient_group', 'body']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'recipient_group': forms.Select(attrs={'class': 'form-select'}),
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
        }
