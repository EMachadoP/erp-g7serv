from django import forms
from django.forms import inlineformset_factory
from .models import ServiceOrder, ServiceOrderItem
from estoque.models import Product

from django.contrib.auth.models import User

class UserFullNameChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        # Retorna "Nome Sobrenome" ou o "Username" se o nome estiver vazio
        return obj.get_full_name() or obj.username.upper()

class ServiceOrderForm(forms.ModelForm):
    technician = UserFullNameChoiceField(
        queryset=User.objects.filter(technician_profile__isnull=False, is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Técnico Responsável",
        required=False
    )
    seller = UserFullNameChoiceField(
        queryset=User.objects.filter(technician_profile__isnull=True, is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Vendedor",
        required=False
    )

    class Meta:
        model = ServiceOrder
        fields = ['client', 'technician', 'seller', 'description', 'status', 'scheduled_date']
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select'}),
            # technician and seller are defined as fields above
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'scheduled_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from core.models import Person
        self.fields['client'].queryset = Person.objects.filter(is_client=True, is_supplier=False)


class ServiceOrderItemForm(forms.ModelForm):
    class Meta:
        model = ServiceOrderItem
        fields = ['product', 'quantity', 'unit_price']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter active products
        self.fields['product'].queryset = Product.objects.filter(active=True)

ServiceOrderItemFormSet = inlineformset_factory(
    ServiceOrder,
    ServiceOrderItem,
    form=ServiceOrderItemForm,
    extra=1,
    can_delete=True
)
