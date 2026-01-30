import os
import django
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from financeiro.models import Expense, Revenue, BankReconciliation

def create_financial_data():
    # Create Expenses
    for i in range(5):
        expense = Expense.objects.create(
            description=f'Despesa Teste {i+1}',
            amount=150.00 * (i+1),
            due_date=timezone.now().date() + timedelta(days=i),
            paid=(i % 2 == 0)
        )
        print(f"Expense created: {expense}")

    # Create Revenues
    for i in range(5):
        revenue = Revenue.objects.create(
            description=f'Receita Teste {i+1}',
            amount=300.00 * (i+1),
            received_date=timezone.now().date() - timedelta(days=i),
            source=f'Cliente {i+1}'
        )
        print(f"Revenue created: {revenue}")

    # Create Reconciliations
    for i in range(3):
        rec = BankReconciliation.objects.create(
            date=timezone.now().date(),
            description=f'Transação Bancária {i+1}',
            amount=50.00 * (i+1),
            transaction_type='CREDIT' if i % 2 == 0 else 'DEBIT'
        )
        print(f"Reconciliation created: {rec}")

if __name__ == '__main__':
    create_financial_data()
