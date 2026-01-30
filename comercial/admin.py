from django.contrib import admin
from .models import BillingGroup, ContractTemplate, Contract, Budget

@admin.register(BillingGroup)
class BillingGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'active')

@admin.register(ContractTemplate)
class ContractTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'active')

from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

def generate_pdf(modeladmin, request, queryset):
    for contract in queryset:
        # Variable Substitution
        content = contract.template.content
        content = content.replace('{{cliente_nome}}', contract.client.name)
        content = content.replace('{{valor}}', str(contract.value))
        
        # Render PDF
        template_path = 'comercial/contract_pdf.html'
        context = {'contract': contract, 'content': content}
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="contrato_{contract.id}.pdf"'
        
        template = get_template(template_path)
        html = template.render(context)
        
        pisa_status = pisa.CreatePDF(html, dest=response)
        
        if pisa_status.err:
            return HttpResponse('We had some errors <pre>' + html + '</pre>')
        
        return response

generate_pdf.short_description = "Gerar PDF do Contrato"

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('client', 'modality', 'value', 'status', 'signed_at')
    list_filter = ('status', 'modality', 'billing_group')
    search_fields = ('client__name',)
    readonly_fields = ('token', 'signed_at', 'signed_ip', 'signature_image')
    actions = [generate_pdf]

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('client', 'date', 'total_value', 'status')
    list_filter = ('status', 'date')
    search_fields = ('client__name',)
