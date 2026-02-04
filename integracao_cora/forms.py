from django import forms
from .models import CoraConfig

class CoraConfigForm(forms.ModelForm):
    class Meta:
        model = CoraConfig
        fields = [
            'client_id', 'client_secret', 'certificado_pem', 'chave_privada', 'ambiente',
            'taxa_multa', 'taxa_juros', 'dias_protesto', 'instrucoes_boleto'
        ]
        widgets = {
            'client_id': forms.TextInput(attrs={'class': 'form-control'}),
            'client_secret': forms.PasswordInput(attrs={'class': 'form-control', 'render_value': True, 'required': False}),
            'certificado_pem': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'chave_privada': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'ambiente': forms.Select(attrs={'class': 'form-select'}),
            'taxa_multa': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'taxa_juros': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'dias_protesto': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'instrucoes_boleto': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
