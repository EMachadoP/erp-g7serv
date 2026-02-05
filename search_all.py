import os
import django
import sys

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from faturamento.models import Invoice
from financeiro.models import AccountReceivable
from comercial.models import Budget, Contract
from operacional.models import ServiceOrder

def search():
    print("--- RECENTLY UPDATED/CANCELLED ITEMS ---")
    
    print("\n[ BUDGETS ]")
    budgets = Budget.objects.order_by('-updated_at')[:5]
    for i in budgets:
        print(f"ID: {i.id}, Title: {i.title}, Client: {i.client.name}, Status: {i.status}, Updated: {i.updated_at}")
        
    print("\n[ CONTRACTS ]")
    contracts = Contract.objects.order_by('-updated_at')[:5]
    for i in contracts:
        print(f"ID: {i.id}, Client: {i.client.name}, Status: {i.status}, Updated: {i.updated_at}")
        
    print("\n[ SERVICE ORDERS ]")
    sos = ServiceOrder.objects.order_by('-updated_at')[:5]
    for i in sos:
        print(f"ID: {i.id}, Client: {i.client.name}, Status: {i.status}, Updated: {i.updated_at}")
        
    print("\n[ INVOICES ]")
    invoices = Invoice.objects.order_by('-updated_at')[:5]
    for i in invoices:
        print(f"ID: {i.id}, Number: {i.number}, Status: {i.status}, Updated: {i.updated_at}")

if __name__ == "__main__":
    search()
