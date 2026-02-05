import os
import django
import sys

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from faturamento.models import Invoice
from financeiro.models import AccountReceivable

def search():
    print("--- RECENTLY CANCELLED INVOICES ---")
    invoices = Invoice.objects.filter(status='CN').order_by('-updated_at')[:10]
    for i in invoices:
        print(f"Invoice ID: {i.id}, Number: {i.number}, Client: {i.client.name if i.client else 'N/A'}, Updated: {i.updated_at}")
    
    print("\n--- RECENTLY CANCELLED RECEIVABLES ---")
    receivables = AccountReceivable.objects.filter(status='CANCELLED').order_by('-updated_at')[:10]
    for r in receivables:
        print(f"Receivable ID: {r.id}, Desc: {r.description}, Updated: {r.updated_at}")

if __name__ == "__main__":
    search()
