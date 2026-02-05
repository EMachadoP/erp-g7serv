
import os
import django
import logging

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
os.environ['SECRET_KEY'] = 'django-insecure-local-dev-key'
os.environ['DEBUG'] = 'True'
django.setup()

from faturamento.models import Invoice
from financeiro.services.email_service import BillingEmailService

# Configure logging to console
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('financeiro.services.email_service')
logger.setLevel(logging.DEBUG)

def diag_email():
    # Try finding by PK 4 or number if necessary
    invoice = Invoice.objects.filter(pk=4).first()
    if not invoice:
        invoice = Invoice.objects.filter(number__icontains='4').first()
    
    if not invoice:
        print("Fatura #4 não encontrada no banco de dados.")
        return

    print(f"Testando envio de e-mail para Fatura: {invoice.number} (ID: {invoice.id})")
    print(f"Cliente: {invoice.client.name if invoice.client else 'N/A'}")
    print(f"E-mail do Cliente: {invoice.client.email if invoice.client else 'N/A'}")
    print(f"Boleto URL: {invoice.boleto_url}")
    
    success = BillingEmailService.send_invoice_email(invoice)
    
    if success:
        print("\nSucesso: E-mail enviado (simulado ou real se BREVO_API_KEY estiver setada).")
    else:
        print("\nFalha: O e-mail não foi enviado. Verifique os logs acima para detalhes.")

if __name__ == "__main__":
    diag_email()
