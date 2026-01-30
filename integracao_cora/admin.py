from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import CoraConfig, BoletoCora

@admin.register(CoraConfig)
class CoraConfigAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'client_id', 'ambiente', 'token_expires_at')
    readonly_fields = ('status_conexao', 'access_token', 'token_expires_at')
    
    def status_conexao(self, obj):
        url = reverse('configuracao_cora')
        if obj.access_token:
            return format_html(
                '<span style="color: green; font-weight: bold;">✅ CONECTADO</span> '
                '<a class="button" href="{}" style="margin-left: 10px;">Reconectar</a>',
                url
            )
        else:
            return format_html(
                '<a class="button" href="{}" style="background-color: #447e9b; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none;">CONECTAR COM A CORA</a>',
                url
            )
    
    status_conexao.short_description = "Status da Conexão"

    def has_add_permission(self, request):
        # Singleton pattern: prevent adding more than one config if one exists
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

@admin.action(description='💰 Simular Pagamento (Sandbox Only)')
def simular_pagamento_sandbox(modeladmin, request, queryset):
    from integracao_cora.services.boleto import CoraBoleto
    from django.contrib import messages
    
    service = CoraBoleto()
    success_count = 0
    
    for boleto in queryset:
        try:
            service.simular_pagamento(boleto)
            success_count += 1
        except Exception as e:
            messages.error(request, f"Erro ao simular pagamento do boleto {boleto.cora_id}: {str(e)}")
            
    if success_count > 0:
        messages.success(request, f"{success_count} pagamento(s) simulado(s)! O dinheiro (fictício) caiu na conta.")

@admin.register(BoletoCora)
class BoletoCoraAdmin(admin.ModelAdmin):
    list_display = ('cora_id', 'cliente', 'valor', 'data_vencimento', 'status', 'ver_boleto', 'created_at')
    list_filter = ('status', 'data_vencimento', 'created_at')
    search_fields = ('cora_id', 'cliente__name', 'cliente__document', 'linha_digitavel')
    readonly_fields = ('cora_id', 'linha_digitavel', 'codigo_barras', 'url_pdf', 'created_at', 'updated_at')
    actions = [simular_pagamento_sandbox]

    def ver_boleto(self, obj):
        if obj.url_pdf:
            return format_html(
                '<a href="{}" target="_blank" style="background:#007bff; color:white; padding:5px 10px; border-radius:4px; text-decoration:none;">🖨️ Imprimir</a>',
                obj.url_pdf
            )
        return '-'
    ver_boleto.short_description = "Boleto"
