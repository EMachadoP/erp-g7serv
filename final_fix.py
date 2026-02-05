import os
import django
import sys

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from faturamento.models import Invoice
from financeiro.models import AccountReceivable, FinancialCategory

def final_fix():
    print("Starting final fix...")
    
    # 1. Update ELDON's invoice status to PG (Paid)
    inv = Invoice.objects.filter(client__name__icontains='ELDON').first()
    if inv:
        print(f"Updating Invoice {inv.number} status to PG")
        inv.status = 'PG'
        inv.save()
        
        # Also update his receivable if it exists
        rec = AccountReceivable.objects.filter(invoice=inv).first()
        if rec:
            print(f"Updating Receivable for {inv.number} to RECEIVED")
            rec.status = 'RECEIVED'
            rec.save()

    # 2. Aggressive Template Sanitization
    path = 'financeiro/templates/financeiro/account_receivable_list.html'
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        import re
        # This regex will catch both [[ and {{ even with newlines
        def clean_tag(match):
            inner = match.group(1).strip().replace('\n', ' ').replace('\r', ' ')
            # Collapse multiple spaces
            inner = ' '.join(inner.split())
            return f"{{{{ {inner} }}}}"
            
        # Replace [[ ... ]]
        content = re.sub(r"\[\[(.*?)\]\]", clean_tag, content, flags=re.DOTALL)
        # Replace {{ ... }} to normalize them and remove newlines
        content = re.sub(r"\{\{(.*?)\}\}", clean_tag, content, flags=re.DOTALL)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Template sanitization complete.")

if __name__ == "__main__":
    final_fix()
