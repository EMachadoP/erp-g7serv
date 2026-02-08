import os
import django
from django.db.models import Sum
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from financeiro.models import FinancialTransaction, CategoriaFinanceira

def debug_dre():
    start_date = '2026-02-01'
    end_date = '2026-02-08'
    
    print(f"--- Debugging DRE ({start_date} to {end_date}) ---")
    
    # Check transactions
    qs = FinancialTransaction.objects.filter(transaction_type='IN', date__range=[start_date, end_date])
    print(f"Total Transactions found: {qs.count()}")
    for t in qs:
        print(f"  - {t.description}: R$ {t.amount} | Cat: {t.category}")
    
    # Replicate view query
    receitas_query = qs.values('category__grupo_dre').annotate(total=Sum('amount')).order_by('category__ordem_exibicao')
    print(f"Grouped Result (Receitas): {list(receitas_query)}")
    
    total_receitas = sum(r['total'] for r in receitas_query)
    print(f"Total Receitas: R$ {total_receitas}")

if __name__ == "__main__":
    debug_dre()
