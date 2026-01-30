
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "erp.settings")
django.setup()

from operacional.models import ServiceOrder
from django.contrib.auth.models import User

print("--- Active Service Orders ---")
orders = ServiceOrder.objects.exclude(status__in=['COMPLETED', 'CANCELED'])
for os in orders:
    tech_name = os.technician.username if os.technician else "None"
    print(f"OS #{os.id} | Status: {os.status} | Technician: {tech_name} | Client: {os.client}")

print("\n--- Users ---")
for u in User.objects.all():
    print(f"User: {u.username} (ID: {u.id}) | Superuser: {u.is_superuser}")
