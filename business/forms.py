from django import forms
from .models import Expense, Vendor, Asset, ExpenseCategory

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['title', 'category', 'amount', 'date', 'vendor', 'description', 'receipt_file']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'vendor': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'receipt_file': forms.FileInput(attrs={'class': 'form-control'}),
        }

class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'service_type': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = '__all__'
        widgets = {
            'purchase_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'condition': forms.Select(attrs={'class': 'form-select'}),
            # Add other widgets as needed, relying on crispy Default mostly
        }
