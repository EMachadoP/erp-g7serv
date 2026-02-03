from django import forms
from .models import AccountPayable, AccountReceivable, CashAccount, CostCenter, FinancialCategory, Receipt
from core.models import Person

class ReceiptForm(forms.ModelForm):
    class Meta:
        model = Receipt
        fields = ['type', 'person', 'amount', 'issue_date', 'description']
        widgets = {
            'type': forms.RadioSelect(attrs={'class': 'btn-check'}),
            'person': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'issue_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['person'].queryset = Person.objects.all()

class AccountPayableForm(forms.ModelForm):
    class Meta:
        model = AccountPayable
        fields = [
            'description', 'supplier', 'category', 'amount', 'due_date', 
            'occurrence_date', 'document_number', 'account', 'cost_center', 
            'payment_method', 'notes', 'status'
        ]
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'occurrence_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'payment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'document_number': forms.TextInput(attrs={'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'account': forms.Select(attrs={'class': 'form-select'}),
            'cost_center': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['supplier'].queryset = Person.objects.filter(is_supplier=True)
        self.fields['category'].queryset = FinancialCategory.objects.filter(type='EXPENSE')

class AccountReceivableForm(forms.ModelForm):
    class Meta:
        model = AccountReceivable
        fields = [
            'description', 'client', 'category', 'amount', 'due_date', 
            'occurrence_date', 'document_number', 'account', 'cost_center', 
            'payment_method', 'notes', 'status', 'external_reference', 
            'fine_amount', 'interest_percent'
        ]
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'occurrence_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'receipt_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'document_number': forms.TextInput(attrs={'class': 'form-control'}),
            'payment_method': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'client': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'account': forms.Select(attrs={'class': 'form-select'}),
            'cost_center': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client'].queryset = Person.objects.filter(is_client=True)
        self.fields['category'].queryset = FinancialCategory.objects.filter(type='REVENUE')

class PaymentPayableForm(forms.Form):
    payment_date = forms.DateField(
        label="Data do Pagamento",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    # This is the "Total a Pagar" that will be calculated
    amount = forms.DecimalField(
        label="Total Pago (R$)",
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'readonly': 'readonly'})
    )
    interest = forms.DecimalField(
        label="Juros (R$)",
        max_digits=12,
        decimal_places=2,
        initial=0,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    fine = forms.DecimalField(
        label="Multa (R$)",
        max_digits=12,
        decimal_places=2,
        initial=0,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    discount = forms.DecimalField(
        label="Desconto (R$)",
        max_digits=12,
        decimal_places=2,
        initial=0,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    account = forms.ModelChoiceField(
        queryset=CashAccount.objects.all(),
        label="Conta de Saída",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    notes = forms.CharField(
        label="Observações",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError("O valor deve ser positivo.")
        return amount
