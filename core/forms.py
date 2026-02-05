from django import forms
from django.contrib.auth.models import User
from .models import Technician

class TechnicianForm(forms.ModelForm):
    username = forms.CharField(label="Usuário", widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label="Senha", widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=False, help_text="Deixe em branco para manter a senha atual (na edição).")
    email = forms.EmailField(label="E-mail", widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(label="Nome", widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label="Sobrenome", widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    phone = forms.CharField(label="Telefone", widget=forms.TextInput(attrs={'class': 'form-control'}), required=False)
    calendar_color = forms.CharField(label="Cor na Agenda", widget=forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}), initial="#0d6efd")
    active = forms.BooleanField(label="Ativo", required=False, initial=True, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

    class Meta:
        model = Technician
        fields = ['phone', 'calendar_color', 'active']

    def __init__(self, *args, **kwargs):
        self.user_instance = kwargs.pop('user_instance', None)
        super().__init__(*args, **kwargs)
        if self.user_instance:
            self.fields['username'].initial = self.user_instance.username
            self.fields['email'].initial = self.user_instance.email
            self.fields['first_name'].initial = self.user_instance.first_name
            self.fields['last_name'].initial = self.user_instance.last_name
            self.fields['password'].required = False
        else:
            self.fields['password'].required = True

    def save(self, commit=True):
        technician = super().save(commit=False)
        
        if self.user_instance:
            user = self.user_instance
        else:
            user = User()
            
        user.username = self.cleaned_data['username']
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if self.cleaned_data['password']:
            user.set_password(self.cleaned_data['password'])
            
        if commit:
            user.save()
            technician.user = user
            technician.save()
            
        return technician

from .models import CompanySettings

class CompanySettingsForm(forms.ModelForm):
    class Meta:
        model = CompanySettings
        fields = ['name', 'cnpj', 'address', 'phone', 'email', 'logo', 'cora_environment', 'cora_client_id', 'cora_cert_base64', 'cora_key_base64']
        widgets = {
            'cora_environment': forms.Select(attrs={'class': 'form-select'}),
            'cora_cert_base64': forms.Textarea(attrs={'rows': 5, 'class': 'form-control font-monospace', 'style': 'font-size: 0.8rem;'}),
            'cora_key_base64': forms.Textarea(attrs={'rows': 5, 'class': 'form-control font-monospace', 'style': 'font-size: 0.8rem;'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'cnpj': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'cora_client_id': forms.TextInput(attrs={'class': 'form-control'}),
        }


from .models import EmailTemplate

class EmailTemplateForm(forms.ModelForm):
    class Meta:
        model = EmailTemplate
        fields = ['name', 'subject', 'body', 'template_type', 'active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Boleto com Nota Fiscal'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Assunto do e-mail'}),
            'body': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 10,
                'placeholder': 'Use placeholders: {cliente}, {valor}, {vencimento}, {fatura}, {link_boleto}, {link_nf}'
            }),
            'template_type': forms.Select(attrs={'class': 'form-select'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

