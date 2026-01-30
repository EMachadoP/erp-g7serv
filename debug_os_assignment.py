
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "erp.settings")
django.setup()

from operacional.models import ServiceOrder
from django.contrib.auth.models import User
from core.models import Technician, Person

print("--- AUDIT: Technician Profiles ---")
for t in Technician.objects.all():
    print(f"Tech ID: {t.id} | User: {t.user.username} | Active: {t.active}")

print("\n--- AUDIT: Collaborative Persons ---")
for p in Person.objects.filter(is_collaborator=True):
    print(f"Person ID: {p.id} | Name: {p.name} | CPF: {p.document}")

print("\n--- AUDIT: OS Assignments (Detailed) ---")
for os in ServiceOrder.objects.exclude(status__in=['COMPLETED', 'CANCELED']):
    tech = os.technician.username if os.technician else "NONE"
    team = os.technical_team.name if os.technical_team else "NONE"
    print(f"OS #{os.id} | Status: {os.status} | Technician (User): {tech} | Technical Team (Person): {team}")
