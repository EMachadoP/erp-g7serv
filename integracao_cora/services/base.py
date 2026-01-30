import tempfile
import os
import contextlib
from cryptography.hazmat.primitives import serialization
from nfse_nacional.models import Empresa
from nfse_nacional.services.assinador import carregar_certificado

@contextlib.contextmanager
def mTLS_cert_paths():
    """
    Context manager that prepares the certificate and private key files for mTLS requests.
    Yields a tuple (cert_path, key_path) to be used in requests.cert.
    """
    from integracao_cora.models import CoraConfig
    
    config = CoraConfig.objects.first()
    if not config:
        raise Exception("Configuração da Cora não encontrada.")
        
    if not config.certificado_pem or not config.chave_privada:
        raise Exception("Certificado PEM e Chave Privada da Cora não configurados.")

    # Since these are FileFields, we can access their paths directly if stored locally.
    # Assuming standard Django FileStorage which stores files on disk.
    # If using cloud storage (S3), we might need to download them to temp files.
    # For now, assuming local filesystem as per previous context (G: drive).
    
    cert_path = config.certificado_pem.path
    key_path = config.chave_privada.path
    
    # Verify files exist
    if not os.path.exists(cert_path) or not os.path.exists(key_path):
        raise Exception("Arquivos de certificado não encontrados no disco.")

    yield (cert_path, key_path)
    
    # No cleanup needed as we are using the stored files directly.
    # If we were downloading from S3, we would clean up here.
