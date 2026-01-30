from django import forms
from .models import BillingGroup

class BillingGroupForm(forms.ModelForm):
    class Meta:
        model = BillingGroup
        fields = ['name', 'active']
