
from django.db import transaction
from django.utils import timezone
from nfse_nacional.models import Empresa, NFSe
from nfse_nacional.services.api_client import NFSeNacionalClient
from core.models import Service
from financeiro.models import NotaFiscalServico

def emitir_nfse(invoice):
    """
    Orchestrates the NFSe emission process for a given Invoice,
    utilizing the 'nfse_nacional' application modules.
    """
    # 1. Start by finding a valid Company configuration
    empresa = Empresa.objects.first()
    if not empresa:
        raise ValueError("Empresa emissora não configurada em NFS-e Nacional > Empresas Emissoras.")
    
    if not empresa.certificado_a1:
        raise ValueError("Certificado digital A1 não configurado para a empresa emissora.")

    # 2. Get or Create Default Service (if Invoice doesn't have specific service logic yet)
    # Ideally, Invoice items should map to Services. For now, we take a default approach.
    service_code = '1.07.01' # Default fallback
    default_service = Service.objects.filter(codigo_tributacao_nacional=service_code).first()
    
    if not default_service:
        # Create a default service placeholder if none exists
        default_service = Service.objects.create(
            name="Serviço Padrão (Suporte Técnico)",
            base_cost=0,
            sale_price=0,
            codigo_tributacao_nacional=service_code,
            codigo_municipio_ibge=empresa.codigo_mun_ibge, 
            description="Serviços de suporte técnico e manutenção."
        )

    client = NFSeNacionalClient()
    
    with transaction.atomic():
        # 3. Create NFSe Record in nfse_nacional app
        # Check if we already have an NFSe for this invoice (using our link in NotaFiscalServico/Invoice)
        
        # We need to maintain the link. The old logic used NotaFiscalServico.
        # We will keep NotaFiscalServico as a wrapper/link or migrate to direct link.
        # For this refactor, let's create the NFSe object and link it if possible, 
        # or just return it so the view can handle the link.
        
        # Check if we already have a wrapper
        try:
             nota_wrapper = invoice.nfs_record
        except Exception:
             nota_wrapper = None
             
        if nota_wrapper and nota_wrapper.status == 'EMITIDA':
             raise ValueError(f"Nota já emitida para Fatura {invoice.number}")

        # Create the actual NFSe object
        nfse = NFSe.objects.create(
            empresa=empresa,
            cliente=invoice.client, # Assuming Person model compatibility
            servico=default_service,
            valor_servico=invoice.amount, # Override value from invoice
            descricao_servico=f"Ref. Fatura {invoice.number}" # Override description
        )
        
        # 4. Transmit to SEFIN
        success, message = client.enviar_dps(nfse)
        
        if not success:
            # Re-raise to be caught by the view and displayed to user
            raise ValueError(f"Erro na emissão: {message}")
            
        return nfse
