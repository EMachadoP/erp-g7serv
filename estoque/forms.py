from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'sku', 'internal_code', 'category', 'brand', 'family', 'location', 
            'cost_price', 'sale_price', 'image', 'ncm', 'cest', 'product_origin', 
            'barcode', 'supplier_code', 'allow_negative_stock', 'can_be_rented', 
            'minimum_stock', 'current_stock', 'active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'sku': forms.TextInput(attrs={'class': 'form-control'}),
            'internal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'brand': forms.Select(attrs={'class': 'form-select'}),
            'family': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.Select(attrs={'class': 'form-select'}),
            'cost_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'sale_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'ncm': forms.TextInput(attrs={'class': 'form-control'}),
            'cest': forms.TextInput(attrs={'class': 'form-control'}),
            'product_origin': forms.Select(attrs={'class': 'form-select'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control'}),
            'supplier_code': forms.TextInput(attrs={'class': 'form-control'}),
            'allow_negative_stock': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_be_rented': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'minimum_stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'current_stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
