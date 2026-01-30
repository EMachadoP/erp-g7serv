from django import forms
from .models import Invoice, NotaEntradaItem, NotaEntradaParcela
from estoque.models import Product

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['billing_group', 'client', 'contract', 'number', 'issue_date', 'due_date', 'amount', 'status']
        widgets = {
            'billing_group': forms.Select(attrs={'class': 'form-select'}),
            'client': forms.Select(attrs={'class': 'form-select select2'}),
            'contract': forms.Select(attrs={'class': 'form-select'}),
            'number': forms.TextInput(attrs={'class': 'form-control'}),
            'issue_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

class NotaEntradaItemForm(forms.ModelForm):
    # This field allows selecting an existing product
    produto = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        required=False,
        label="Vincular Produto",
        widget=forms.Select(attrs={'class': 'form-select select2'})
    )
    
    # We add a boolean to create new if needed, but the main logic will be:
    # If 'produto' is selected -> Link. 
    # If not -> Create New using XML data (handled in view/form processing).
    create_new = forms.BooleanField(
        required=False, 
        label="Cadastrar Novo",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = NotaEntradaItem
        fields = ['produto']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Customize label to show relevant info
            self.xml_data = f"{self.instance.xProd} (Cód: {self.instance.cProd})"

class NotaEntradaParcelaForm(forms.ModelForm):
    class Meta:
        model = NotaEntradaParcela
        fields = ['numero_parcela', 'data_vencimento', 'valor', 'forma_pagamento']
        widgets = {
            'numero_parcela': forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control-plaintext'}),
            'data_vencimento': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'forma_pagamento': forms.Select(attrs={'class': 'form-select'}),
        }
