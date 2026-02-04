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
    
    import base64
    
    config = CoraConfig.objects.first()
    if not config:
        raise Exception("Configuração da Cora não encontrada.")
        
    # Get cert content from B64 fields (DB) or FileFields (Disk)
    cert_content = None
    key_content = None
    
    if config.certificado_pem_b64:
        cert_content = base64.b64decode(config.certificado_pem_b64)
    elif config.certificado_pem:
        try:
            config.certificado_pem.open('rb')
            cert_content = config.certificado_pem.read()
        except: pass

    if config.chave_privada_b64:
        key_content = base64.b64decode(config.chave_privada_b64)
    elif config.chave_privada:
        try:
            config.chave_privada.open('rb')
            key_content = config.chave_privada.read()
        except: pass

    if not cert_content or not key_content:
        raise Exception("Certificado PEM e Chave Privada da Cora não configurados no Banco (B64) nem no Disco.")

    # Create temporary files
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pem') as cert_file, \
         tempfile.NamedTemporaryFile(delete=False, suffix='.key') as key_file:
        
        cert_file.write(cert_content)
        key_file.write(key_content)
        
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
