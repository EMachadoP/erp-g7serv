from django.contrib import admin
from .models import BillingGroup, ContractTemplate, Contract, Budget, MaintenanceService

@admin.register(MaintenanceService)
class MaintenanceServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'active')
    list_editable = ('order', 'active')
    search_fields = ('name',)


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
    list_display = ('id', 'client', 'date', 'total_value', 'status', 'origin', 'seller')
    list_filter = ('status', 'date', 'origin', 'seller', 'commission_paid')
    search_fields = ('client__name', 'id')
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('client', 'title', 'seller', 'status', 'origin', 'date', 'validity_date')
        }),
        ('Comissionamento', {
            'fields': ('technician', 'seller_commission_pct', 'technician_commission_pct', 'gratification_value', 'commission_paid', 'closing_date')
        }),
        ('Valores e Pagamento', {
            'fields': ('total_value', 'payment_method', 'payment_details')
        }),
        ('Endereço e Observações', {
            'fields': ('address', 'contact', 'observation', 'approved_by_operations', 'followup_strategy', 'last_followup')
        }),
    )
