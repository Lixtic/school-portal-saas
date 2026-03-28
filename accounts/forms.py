from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, UserSettings

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'address', 'profile_picture')

class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone', 'address', 'profile_picture')


class UserProfileForm(forms.ModelForm):
    """Self-service profile update form shown on the user settings page."""
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone', 'address', 'profile_picture')
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')
        self.fields['profile_picture'].widget.attrs['class'] = 'form-control'


class UserSettingsForm(forms.ModelForm):
    """Notification and UI preference form."""
    class Meta:
        model = UserSettings
        fields = (
            'notify_announcements',
            'notify_grades',
            'notify_attendance',
            'notify_messages',
            'email_notifications',
            'compact_view',
        )
        widgets = {f: forms.CheckboxInput(attrs={'class': 'form-check-input'}) for f in fields}
