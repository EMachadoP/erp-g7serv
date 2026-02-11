from django import forms
from django.db.models import Q
from django.utils import timezone
from .models import (
    AccountPayable, AccountReceivable, CashAccount, CentroResultado, 
    CategoriaFinanceira, Receipt, EmpresaFiscal, ConfiguracaoComissao
)

class ConfiguracaoComissaoForm(forms.ModelForm):
    class Meta:
        model = ConfiguracaoComissao
        fields = ['pct_vendedor', 'pct_tecnico']
        widgets = {
            'pct_vendedor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'pct_tecnico': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class EmpresaFiscalForm(forms.ModelForm):
    class Meta:
        model = EmpresaFiscal
        fields = [
            'cnpj', 'inscricao_municipal', 'codigo_municipio_ibge', 
            'regime_tributario', 'ultimo_numero_dps', 'ultimo_numero_nfse',
            'cnae_padrao', 'codigo_servico_lc116_padrao',
            'certificado_a1_base64', 'senha_certificado'
        ]
        widgets = {
            'cnpj': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apenas números'}),
            'inscricao_municipal': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_municipio_ibge': forms.TextInput(attrs={'class': 'form-control'}),
            'regime_tributario': forms.Select(choices=[(1, 'Simples Nacional'), (2, 'Regime Normal')], attrs={'class': 'form-select'}),
            'ultimo_numero_dps': forms.NumberInput(attrs={'class': 'form-control'}),
            'ultimo_numero_nfse': forms.NumberInput(attrs={'class': 'form-control'}),
            'cnae_padrao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 6202300'}),
            'codigo_servico_lc116_padrao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 1.05'}),
            'certificado_a1_base64': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Cole aqui a string Base64 do certificado'}),
            'senha_certificado': forms.PasswordInput(render_value=True, attrs={'class': 'form-control'}),
        }
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
            'payment_method', 'notes', 'status', 'current_installment', 'total_installments',
            'is_recurring', 'recurrence_period'
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
            'current_installment': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'total_installments': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'is_recurring': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'recurrence_period': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['supplier'].queryset = Person.objects.all().order_by('name')
        self.fields['category'].queryset = CategoriaFinanceira.objects.filter(tipo='saida')
        
        # Define a data da ocorrência como hoje por padrão
        if not self.instance.pk:
            self.fields['occurrence_date'].initial = timezone.now().date()

class AccountReceivableForm(forms.ModelForm):
    class Meta:
        model = AccountReceivable
        fields = [
            'description', 'client', 'category', 'amount', 'due_date', 
            'occurrence_date', 'document_number', 'account', 'cost_center', 
            'payment_method', 'notes', 'status', 'external_reference', 
            'fine_amount', 'interest_percent', 'current_installment', 'total_installments'
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
            'external_reference': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: NF 123'}),
            'fine_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'interest_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'current_installment': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'total_installments': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client'].queryset = Person.objects.all().order_by('name')
        self.fields['category'].queryset = CategoriaFinanceira.objects.filter(tipo='entrada')

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

class CashAccountForm(forms.ModelForm):
    class Meta:
        model = CashAccount
        fields = ['name', 'bank_name', 'agency', 'account_number', 'initial_balance']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Cora Principal'}),
            'bank_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Cora'}),
            'agency': forms.TextInput(attrs={'class': 'form-control'}),
            'account_number': forms.TextInput(attrs={'class': 'form-control'}),
            'initial_balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class CategoriaFinanceiraForm(forms.ModelForm):
    class Meta:
        model = CategoriaFinanceira
        fields = ['nome', 'tipo', 'grupo_dre', 'ordem_exibicao', 'parent']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'grupo_dre': forms.TextInput(attrs={'class': 'form-control'}),
            'ordem_exibicao': forms.NumberInput(attrs={'class': 'form-control'}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
        }

class CentroResultadoForm(forms.ModelForm):
    class Meta:
        model = CentroResultado
        fields = ['nome', 'ativo', 'code']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
        }
