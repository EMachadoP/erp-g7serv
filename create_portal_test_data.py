import os
import django
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Person
from portal.models import ClientProfile
from comercial.models import Contract, BillingGroup, ContractTemplate
from faturamento.models import Invoice
from operacional.models import ServiceOrder

def create_test_data():
    # Create User
    user, created = User.objects.get_or_create(username='testclient', email='client@example.com')
    if created:
        user.set_password('password123')
        user.save()
        print(f"User {user.username} created.")
    else:
        print(f"User {user.username} already exists.")

    # Create Person (Client)
    person, created = Person.objects.get_or_create(name='Test Client Company', person_type='J', document='12345678000199')
    if created:
        print(f"Person {person.name} created.")
    else:
        print(f"Person {person.name} already exists.")

    # Create ClientProfile
    profile, created = ClientProfile.objects.get_or_create(user=user, person=person)
    if created:
        print(f"ClientProfile created for {user.username}.")
    else:
        print(f"ClientProfile already exists for {user.username}.")

    # Create Contract Template
    template, created = ContractTemplate.objects.get_or_create(name='Standard Template', content='Standard Content')

    # Create Contract and Billing Group (needed for Invoice)
    contract, created = Contract.objects.get_or_create(
        client=person, 
        defaults={
            # 'description': 'Test Contract', # Removed as it is not a valid field
            'template': template,
            'start_date': timezone.now().date(),
            'due_day': 10,
            'value': 1000.00
        }
    )
    
    if created:
         # Create Billing Group if not exists (Contract has billing_group FK, but it can be null. 
         # However, Invoice needs billing_group.
         # Let's create a billing group and assign it to the contract.
         billing_group = BillingGroup.objects.create(name='Test Group')
         contract.billing_group = billing_group
         contract.save()
    else:
         if contract.billing_group:
             billing_group = contract.billing_group
         else:
             billing_group = BillingGroup.objects.create(name='Test Group')
             contract.billing_group = billing_group
             contract.save()

    # Create Invoices
    for i in range(3):
        invoice, created = Invoice.objects.get_or_create(
            billing_group=billing_group,
            number=f'INV-00{i+1}',
            defaults={
                'issue_date': timezone.now().date(),
                'due_date': timezone.now().date() + timedelta(days=10),
                'amount': 100.00 * (i+1),
                'status': 'PENDING'
            }
        )
        if created:
            print(f"Invoice {invoice.number} created.")

    # Create Service Orders
    for i in range(3):
        os, created = ServiceOrder.objects.get_or_create(
            client=person,
            product=f'Service {i+1}',
            defaults={
                'start_date': timezone.now(),
                'status': 'OPEN'
            }
        )
        if created:
            print(f"ServiceOrder {os.id} created.")

if __name__ == '__main__':
    create_test_data()
