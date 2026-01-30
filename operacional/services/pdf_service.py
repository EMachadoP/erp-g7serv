from django.template.loader import get_template
from xhtml2pdf import pisa
from django.http import HttpResponse
from django.conf import settings
from core.models import CompanySettings
import os
import io
import re
from django.utils import timezone

def get_checklist_filename(order):
    """
    Generates a filename based on client name and date.
    Format: [ClientShortName]_[DD]_[MM]_[YYYY].pdf
    """
    client_name = order.client.fantasy_name or order.client.name
    # Clean name: remove special chars and spaces
    clean_name = re.sub(r'[^\w\s-]', '', client_name).strip()
    clean_name = re.sub(r'[\s]+', '_', clean_name)
    
    date_str = timezone.now().strftime('%d_%m_%Y')
    return f"{clean_name}_{date_str}.pdf"

def generate_preventive_pdf_bytes(order, categories, responses):
    """
    Returns the PDF content as bytes.
    """
    template = get_template('operacional/checklist_pdf_template.html')
    company_settings = CompanySettings.objects.first()
    
    # Calculate Summary Stats
    total_items = 0
    ok_items = 0
    fail_items = 0
    nd_items = 0
    
    for resp in responses.values():
        total_items += 1
        val = (resp.resposta_valor or '').upper()
        if val == 'SIM':
            ok_items += 1
        elif val == 'NÃO':
            fail_items += 1
        elif val == 'N/D':
            nd_items += 1
            
    context = {
        'order': order,
        'categories': categories,
        'responses': responses,
        'company': company_settings,
        'summary': {
            'total': total_items,
            'ok': ok_items,
            'fail': fail_items,
            'nd': nd_items
        },
    }
    
    html = template.render(context)
    result = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.BytesIO(html.encode("utf-8")), dest=result, encoding='utf-8')
    
    if pisa_status.err:
        return None
    return result.getvalue()

def render_preventive_pdf(order, categories, responses):
    pdf_content = generate_preventive_pdf_bytes(order, categories, responses)
    if not pdf_content:
        return HttpResponse('Erro ao gerar PDF', status=500)
        
    filename = get_checklist_filename(order)
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
