import os
import django
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from core.models import Person
from operational.models import ServiceOrder

def create_operational_data():
    # Ensure clients exist
    clients = Person.objects.filter(is_client=True)
    if not clients.exists():
        print("No clients found. Please run commercial test data script first.")
        return

    # Create Service Orders
    for i, client in enumerate(clients):
        order = ServiceOrder.objects.create(
            client=client,
            product=f'Manutenção Equipamento {i+1}',
            description='Manutenção preventiva e corretiva...',
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=5),
            value=1500.00 * (i+1),
            status='PENDING' if i % 2 == 0 else 'IN_PROGRESS'
        )
        print(f"Service Order created: {order}")

if __name__ == '__main__':
    try:
        from operational.models import ServiceOrder
    except ImportError:
        # Fallback if app name is 'operacional' (Portuguese)
        from operacional.models import ServiceOrder
        
    create_operational_data()
