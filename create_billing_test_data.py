import os
import django
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from comercial.models import BillingGroup
from faturamento.models import Invoice

def create_billing_data():
    # Ensure billing groups exist (from commercial data)
    billing_groups = BillingGroup.objects.all()
    if not billing_groups.exists():
        # Create a dummy billing group if none exists
        from comercial.models import Contract
        contract = Contract.objects.first()
        if contract:
            group = BillingGroup.objects.create(
                contract=contract,
                name=f'Grupo Faturamento - {contract.client.name}'
            )
            billing_groups = [group]
            print(f"Created BillingGroup: {group}")
        else:
            print("No contracts found. Please run commercial test data script first.")
            return

    # Create Invoices
    for i, group in enumerate(billing_groups):
        invoice = Invoice.objects.create(
            billing_group=group,
            number=f'FAT-{timezone.now().year}-{i+1:04d}',
            issue_date=timezone.now().date(),
            due_date=timezone.now().date() + timedelta(days=10),
            amount=1000.00 * (i+1),
            status='PD'
        )
        print(f"Invoice created: {invoice}")

if __name__ == '__main__':
    create_billing_data()
