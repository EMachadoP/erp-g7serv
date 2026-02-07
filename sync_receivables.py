import os
import django
import sys

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from faturamento.models import Invoice
from financeiro.models import AccountReceivable, CategoriaFinanceira

def sync_receivables():
    print("Starting sync...")
    invoices = Invoice.objects.all()
    created_count = 0
    
    category, _ = CategoriaFinanceira.objects.get_or_create(
        nome="Receita de Faturas",
        defaults={'tipo': 'entrada', 'grupo_dre': '1. Receita Bruta', 'ordem_exibicao': 1}
    )
    
    for inv in invoices:
        if not AccountReceivable.objects.get_queryset().filter(invoice=inv).exists():
            print(f"Fixing Invoice: {inv.number} - {inv.client.name if inv.client else 'No Client'}")
            description = f"Fatura #{inv.number}"
            if inv.client:
                description += f" - {inv.client.name}"
            
            AccountReceivable.objects.create(
                description=description,
                client=inv.client,
                category=category,
                amount=inv.amount,
                due_date=inv.due_date,
                status='PENDING' if inv.status == 'PD' else ('RECEIVED' if inv.status == 'PG' else 'CANCELLED'),
                invoice=inv,
                document_number=inv.number
            )
            created_count += 1
            
    print(f"Sync complete. Created {created_count} missing receivables.")

if __name__ == "__main__":
    sync_receivables()
