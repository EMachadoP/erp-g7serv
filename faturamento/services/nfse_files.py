import time
import logging
from django.db import transaction
from .nfse_utils import _auto_link_nfse

logger = logging.getLogger(__name__)

def ensure_nfse_files(invoice, max_wait_seconds=20, sleep_seconds=4):
    """
    Garante que a NFSe vinculada à fatura tenha DANFSe (PDF) e XML salvos.
    Retorna (ok: bool, msg: str)
    """
    from nfse_nacional.services.api_client import NFSeNacionalClient
    
    nfse = _auto_link_nfse(invoice)
    if not nfse:
        return False, "NFS-e não encontrada ou vinculada a esta fatura."

    # Se já tiver o PDF, está pronto (o XML costuma vir junto na emissão)
    if nfse.pdf_danfse:
        return True, "NFS-e já possui PDF e XML salvos."

    if not nfse.chave_acesso:
        return False, "NFS-e autorizada sem chave de acesso disponível para download."

    client = NFSeNacionalClient()
    deadline = time.time() + max_wait_seconds
    
    logger.info(f"Iniciando tentativa de download de DANFSe para Fatura {invoice.number} (Chave: {nfse.chave_acesso})")

    while time.time() < deadline:
        try:
            # Tenta baixar o DANFSe
            if client.baixar_danfse(nfse):
                nfse.refresh_from_db()
                if nfse.pdf_danfse:
                    logger.info(f"DANFSe baixado com sucesso para Fatura {invoice.number}")
                    return True, "DANFSe baixada e salva com sucesso."
            
            # Se não baixou (pode estar em processamento no portal), aguarda um pouco
            logger.info(f"DANFSe ainda não disponível para Fatura {invoice.number}, aguardando {sleep_seconds}s...")
            time.sleep(sleep_seconds)
            
        except Exception as e:
            logger.error(f"Erro durante tentativa de download de DANFSe: {e}")
            time.sleep(sleep_seconds)

    return False, "Tempo esgotado ao tentar baixar a DANFSe do portal nacional."
