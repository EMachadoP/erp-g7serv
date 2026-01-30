import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from comercial.models import Contract

def test_conversion(raw_value):
    print(f"\nTesting raw value: '{raw_value}'")
    if ',' in raw_value:
        converted = raw_value.replace('.', '').replace(',', '.')
    else:
        converted = raw_value
    print(f"Converted string: '{converted}'")
    try:
        decimal_val = Decimal(converted)
        print(f"Decimal value: {decimal_val}")
    except Exception as e:
        print(f"Error converting to Decimal: {e}")

# Test cases
test_conversion("1.500,00")
test_conversion("1500,00")
test_conversion("1500.00")
test_conversion("1.500.000,00")
test_conversion("1500000,00")

# Check current value of Contract 5
try:
    c = Contract.objects.get(id=5)
    print(f"\nCurrent Contract 5 Value: {c.value}")
except Contract.DoesNotExist:
    print("Contract 5 not found")
