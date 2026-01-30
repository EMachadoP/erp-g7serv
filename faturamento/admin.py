from django.contrib import admin
from .models import Invoice
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

def generate_invoice_pdf(modeladmin, request, queryset):
    for invoice in queryset:
        template_path = 'faturamento/invoice_pdf.html'
        context = {'invoice': invoice}
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="fatura_{invoice.number}.pdf"'
        template = get_template(template_path)
        html = template.render(context)
        pisa_status = pisa.CreatePDF(html, dest=response)
        if pisa_status.err:
            return HttpResponse('Erro ao gerar PDF')
        return response

generate_invoice_pdf.short_description = "Gerar PDF da fatura"

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('number', 'billing_group', 'issue_date', 'due_date', 'amount', 'status')
    list_filter = ('status', 'issue_date')
    search_fields = ('number', 'billing_group__name')
    actions = [generate_invoice_pdf]
