import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from comercial.models import Contract

try:
    c = Contract.objects.get(id=5)
    print(f"Old Value: {c.value}")
    c.value = Decimal('1500.00')
    c.save()
    print(f"New Value: {c.value}")
except Contract.DoesNotExist:
    print("Contract 5 not found")
