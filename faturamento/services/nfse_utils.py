from django.db import models

def _auto_link_nfse(invoice):
    """Tenta vincular automaticamente uma NFSe órfã à fatura."""
    if invoice.nfse_record:
        return invoice.nfse_record
        
    from nfse_nacional.models import NFSe as NFSeNacional
    
    # Busca por descrição contendo o número da fatura
    nfse = NFSeNacional.objects.filter(
        descricao_servico__icontains=f'Ref. Fatura {invoice.number}'
    ).first()
    
    if not nfse:
        # Tenta buscar por cliente + status Autorizada
        nfse = NFSeNacional.objects.filter(
            cliente=invoice.client, 
            status='Autorizada'
        ).order_by('-data_emissao').first()
        
    if nfse:
        invoice.nfse_record = nfse
        invoice.save(update_fields=['nfse_record'])
        
    return nfse
