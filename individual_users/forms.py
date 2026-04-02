from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailSignupForm(forms.Form):
    full_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={
        'placeholder': 'Full name', 'autocomplete': 'name',
    }))
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'placeholder': 'you@example.com', 'autocomplete': 'email',
    }))
    password = forms.CharField(min_length=8, widget=forms.PasswordInput(attrs={
        'placeholder': 'Create a password', 'autocomplete': 'new-password',
    }))

    def clean_email(self):
        email = self.cleaned_data['email'].lower().strip()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email


class PhoneSignupForm(forms.Form):
    full_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={
        'placeholder': 'Full name', 'autocomplete': 'name',
    }))
    phone = forms.CharField(max_length=20, widget=forms.TextInput(attrs={
        'placeholder': '+233 XX XXX XXXX', 'autocomplete': 'tel', 'type': 'tel',
    }))
    password = forms.CharField(min_length=8, widget=forms.PasswordInput(attrs={
        'placeholder': 'Create a password', 'autocomplete': 'new-password',
    }))

    def clean_phone(self):
        from individual_users.models import IndividualProfile
        phone = self.cleaned_data['phone'].strip()
        if IndividualProfile.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError('An account with this phone number already exists.')
        return phone


class EmailSigninForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'placeholder': 'you@example.com', 'autocomplete': 'email',
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Password', 'autocomplete': 'current-password',
    }))


class PhoneSigninForm(forms.Form):
    phone = forms.CharField(max_length=20, widget=forms.TextInput(attrs={
        'placeholder': '+233 XX XXX XXXX', 'autocomplete': 'tel', 'type': 'tel',
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Password', 'autocomplete': 'current-password',
    }))


class APIKeyForm(forms.Form):
    name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={
        'placeholder': 'e.g. Production Key',
    }))
