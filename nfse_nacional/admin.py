from django.contrib import admin
from django.contrib import messages
from .models import Empresa, NFSe
from .services.api_client import NFSeNacionalClient

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('razao_social', 'cnpj', 'ambiente')
    search_fields = ('razao_social', 'cnpj')

@admin.action(description='Transmitir para Receita Federal')
def transmitir_nfse(modeladmin, request, queryset):
    client = NFSeNacionalClient()
    success_count = 0
    error_count = 0
    
    for nfse in queryset:
        if nfse.status == 'Autorizada':
            messages.warning(request, f"DPS {nfse.numero_dps} já está autorizada.")
            continue
            
        success, message = client.enviar_dps(nfse)
        if success:
            success_count += 1
        else:
            error_count += 1
            messages.error(request, f"Erro DPS {nfse.numero_dps}: {message}")
            
    if success_count > 0:
        messages.success(request, f"{success_count} nota(s) transmitida(s) com sucesso.")

@admin.action(description='Gerar Boleto Cora')
def gerar_boleto_cora(modeladmin, request, queryset):
    # Allows generation for any status (Pendente, Rejeitada, Autorizada)
    from integracao_cora.services.boleto import CoraBoleto
    service = CoraBoleto()
    success_count = 0
    
    for nfse in queryset:
        try:
            service.gerar_boleto(nfse)
            success_count += 1
        except Exception as e:
            messages.error(request, f"Erro ao gerar boleto para DPS {nfse.numero_dps}: {str(e)}")
            
    if success_count > 0:
        messages.success(request, f"{success_count} boleto(s) gerado(s) com sucesso.")

@admin.register(NFSe)
class NFSeAdmin(admin.ModelAdmin):
    list_display = ('numero_dps', 'serie_dps', 'data_emissao', 'empresa', 'cliente', 'status')
    list_filter = ('status', 'data_emissao', 'empresa')
    search_fields = ('numero_dps', 'cliente__name', 'chave_acesso')
    actions = [transmitir_nfse, gerar_boleto_cora]
    readonly_fields = ('numero_dps', 'data_emissao', 'chave_acesso', 'xml_envio', 'xml_retorno', 'json_erro')
