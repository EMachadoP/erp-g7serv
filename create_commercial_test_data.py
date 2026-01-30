import os
import django
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from core.models import Person
from comercial.models import Contract, Budget, ContractTemplate, BillingGroup

def create_commercial_data():
    # Create Clients
    for i in range(3):
        client, created = Person.objects.get_or_create(
            document=f'111222333000{i+1}',
            defaults={
                'name': f'Cliente Comercial {i+1}',
                'fantasy_name': f'Empresa {i+1}',
                'person_type': 'PJ',
                'is_client': True,
                'email': f'cliente{i+1}@example.com',
                'phone': '11999999999',
                'address': 'Rua Teste',
                'number': str(100 + i),
                'neighborhood': 'Centro',
                'city': 'São Paulo',
                'state': 'SP'
            }
        )
        if created:
            print(f"Client created: {client}")
        else:
            print(f"Client already exists: {client}")

    # Create Contract Template
    template, created = ContractTemplate.objects.get_or_create(
        name='Contrato Padrão de Serviços',
        defaults={'content': '<p>Contrato de prestação de serviços entre <strong>{{cliente_nome}}</strong> e a empresa...</p>'}
    )

    # Create Contracts
    clients = Person.objects.filter(is_client=True)[:3]
    for client in clients:
        contract, created = Contract.objects.get_or_create(
            client=client,
            defaults={
                'template': template,
                'modality': 'Mensal',
                'due_day': 5,
                'value': 2500.00,
                'status': 'Ativo',
                'start_date': timezone.now().date()
            }
        )
        if created:
            print(f"Contract created for {client}")

    # Create Budgets
    for client in clients:
        budget, created = Budget.objects.get_or_create(
            client=client,
            date=timezone.now().date(),
            defaults={
                'status': 'Enviado',
                'validity_date': timezone.now().date() + timedelta(days=15),
                'total_value': 5000.00,
                'description': '<ul><li>Serviço de Consultoria</li><li>Implementação de Sistema</li></ul>'
            }
        )
        if created:
            print(f"Budget created for {client}")

if __name__ == '__main__':
    create_commercial_data()
