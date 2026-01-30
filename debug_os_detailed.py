
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "erp.settings")
django.setup()

from operacional.models import ServiceOrder
from django.contrib.auth.models import User
from django.db.models import Q

print("--- AUDIT: Users ---")
for u in User.objects.all():
    print(f"ID: {u.id:2} | User: {u.username:15} | Super: {u.is_superuser!s:5} | Staff: {u.is_staff!s:5}")

print("\n--- AUDIT: Active Service Orders (Normal Query) ---")
# This is what the view does
status_visiveis = ['PENDING', 'IN_PROGRESS', 'WAITING_MATERIAL', 'OPEN', 'SCHEDULED']
all_active = ServiceOrder.objects.filter(status__in=status_visiveis)
print(f"Total OS with active statuses: {all_active.count()}")

for os in all_active:
    tech = os.technician.username if os.technician else "NONE"
    active_flag = getattr(os, 'active', 'N/A')
    print(f"OS #{os.id:2} | Status: {os.status:10} | Tech: {tech:15} | Active: {active_flag}")

print("\n--- AUDIT: Potential Status Mismatch ---")
distinct_statuses = ServiceOrder.objects.values_list('status', flat=True).distinct()
print(f"Statuses found in DB: {list(distinct_statuses)}")
