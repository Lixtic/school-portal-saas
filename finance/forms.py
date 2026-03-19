from django import forms
from .models import FeeHead, FeeStructure, Payment, StudentFee
from academics.models import Class, AcademicYear

class FeeHeadForm(forms.ModelForm):
    class Meta:
        model = FeeHead
        fields = ['name', 'description']

class FeeStructureForm(forms.ModelForm):
    class Meta:
        model = FeeStructure
        fields = ['head', 'class_level', 'academic_year', 'term', 'amount', 'due_date']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['academic_year'].queryset = AcademicYear.objects.filter(is_current=True)

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'date', 'method', 'reference', 'remarks']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        self._fee = kwargs.pop('fee', None)
        super().__init__(*args, **kwargs)
        self.fields['reference'].widget.attrs['readonly'] = True
        self.fields['reference'].help_text = 'Auto-generated. Will be assigned if left blank.'

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise forms.ValidationError("Payment amount must be greater than zero.")
        if amount is not None and self._fee is not None and amount > self._fee.balance:
            raise forms.ValidationError(
                f"Amount exceeds outstanding balance of ₵{self._fee.balance:.2f}."
            )
        return amount
