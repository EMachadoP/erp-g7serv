from django import forms
from .models import BillingGroup, Contract, ContractItem
from django.forms import inlineformset_factory

class BillingGroupForm(forms.ModelForm):
    class Meta:
        model = BillingGroup
        fields = ['name', 'due_day', 'active']

class ContractForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = [
            'client', 'template', 'billing_group', 'modality', 
            'due_day', 'status', 'start_date', 'end_date', 'maintenance_services'
        ]
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select select2'}),
            'template': forms.Select(attrs={'class': 'form-select'}),
            'billing_group': forms.Select(attrs={'class': 'form-select'}),
            'modality': forms.Select(attrs={'class': 'form-select'}),
            'due_day': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'maintenance_services': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        }

class ContractItemForm(forms.ModelForm):
    class Meta:
        model = ContractItem
        fields = ['category', 'financial_category', 'description', 'quantity', 'unit_price']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'financial_category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Descrição do serviço'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '1'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

ContractItemFormSet = inlineformset_factory(
    Contract, ContractItem, form=ContractItemForm,
    extra=1, can_delete=True
)
