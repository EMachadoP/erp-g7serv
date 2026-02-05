from django.template.loader import get_template
from xhtml2pdf import pisa
from django.core.files.base import ContentFile
from core.models import CompanySettings
import io
import logging

logger = logging.getLogger(__name__)

def generate_invoice_pdf_file(invoice):
    """
    Gera o PDF da fatura e salva no campo pdf_fatura do modelo.
    Retorna os bytes do PDF gerado ou None em caso de erro.
    """
    try:
        company = CompanySettings.objects.first()
        template_path = 'faturamento/invoice_pdf.html'
        context = {
            'invoice': invoice,
            'company': company,
        }
        template = get_template(template_path)
        html = template.render(context)
        
        # Buffer de memória para o PDF
        result = io.BytesIO()
        pisa_status = pisa.CreatePDF(html, dest=result)
        
        if pisa_status.err:
            logger.error(f"Erro ao gerar PDF para fatura {invoice.number}")
            return False
        
        # Salva o arquivo no modelo
        filename = f"fatura_{invoice.number}.pdf"
        pdf_bytes = result.getvalue()
        invoice.pdf_fatura.save(filename, ContentFile(pdf_bytes), save=True)
        logger.info(f"PDF da fatura {invoice.number} gerado e salvo com sucesso.")
        return pdf_bytes
    except Exception as e:
        logger.error(f"Exceção ao gerar PDF da fatura {invoice.number}: {e}")
        return None
