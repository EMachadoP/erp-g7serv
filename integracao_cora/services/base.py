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

    # Create temporary files for the cert and key
    # Railway/Cloud environments have ephemeral filesystems, so we extract from DB to temp files
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pem') as cert_file, \
         tempfile.NamedTemporaryFile(delete=False, suffix='.key') as key_file:
        
        cert_file.write(config.certificado_pem.read())
        key_file.write(config.chave_privada.read())
        
        cert_path = cert_file.name
        key_path = key_file.name

    try:
        yield (cert_path, key_path)
    finally:
        # Cleanup temporary files after use
        if os.path.exists(cert_path):
            os.remove(cert_path)
        if os.path.exists(key_path):
            os.remove(key_path)
    
    # No cleanup needed as we are using the stored files directly.
    # If we were downloading from S3, we would clean up here.
