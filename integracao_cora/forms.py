from django import forms
from .models import CoraConfig

class CoraConfigForm(forms.ModelForm):
    class Meta:
        model = CoraConfig
        fields = ['client_id', 'client_secret', 'certificado_pem', 'chave_privada', 'ambiente']
        widgets = {
            'client_id': forms.TextInput(attrs={'class': 'form-control'}),
            'client_secret': forms.PasswordInput(attrs={'class': 'form-control', 'render_value': True, 'required': False}),
            'certificado_pem': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'chave_privada': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'ambiente': forms.Select(attrs={'class': 'form-select'}),
        }
