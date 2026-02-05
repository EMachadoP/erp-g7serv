
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
os.environ['SECRET_KEY'] = 'django-insecure-local-dev-key'
os.environ['DEBUG'] = 'True'
django.setup()

from faturamento.models import Invoice
from faturamento.services.invoice_service import generate_invoice_pdf_file

def test_gen():
    invoice = Invoice.objects.first()
    if not invoice:
        print("No invoices found to test.")
        return
    
    print(f"Testing PDF generation for invoice {invoice.number}...")
    pdf_bytes = generate_invoice_pdf_file(invoice)
    
    if pdf_bytes:
        print(f"Success! PDF size: {len(pdf_bytes)} bytes")
    else:
        print("Failed to generate PDF.")

if __name__ == "__main__":
    test_gen()
