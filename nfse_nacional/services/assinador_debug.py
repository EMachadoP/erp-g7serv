import sys
import os
import django

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django just in case we need models, but likely we can run standalone if we mock inputs
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from nfse_nacional.models import Empresa
from nfse_nacional.services.assinador import carregar_certificado, assinar_xml
import base64

def test_crash():
    print("--- INICIANDO TESTE DE CRASH (ASSINADOR) ---")
    empresa = Empresa.objects.first()
    if not empresa:
        print("SEM EMPRESA. Fim.")
        return

    print("1. Carregando certificado...")
    cert_bytes = None
    if empresa.certificado_base64:
        cert_bytes = base64.b64decode(empresa.certificado_base64)
    elif empresa.certificado_a1:
        with empresa.certificado_a1.open("rb") as f:
            cert_bytes = f.read()
    
    if not cert_bytes:
        print("SEM CERTIFICADO. Fim.")
        return
        
    print(f"   Bytes lidos: {len(cert_bytes)}")
    
    print("2. Testando carregar_certificado (OpenSSL/Cryptography)...")
    try:
        priv, cert = carregar_certificado(cert_bytes, empresa.senha_certificado)
        print("   SUCESSO carregar_certificado (não crashou).")
    except Exception as e:
        print(f"   ERRO carregar_certificado: {e}")
        return

    print("3. Testando assinar_xml (LXML/SignXML - MOMENTO CRITICO)...")
    dummy_xml = "<InfDPS Id='DPS123'><Test>123</Test></InfDPS>"
    try:
        # This is where segfaults usually happen
        signed = assinar_xml(dummy_xml, cert_bytes, empresa.senha_certificado)
        print("   SUCESSO assinar_xml (não crashou).")
        print(f"   Tamanho assinado: {len(signed)}")
    except Exception as e:
        print(f"   ERRO Python assinar_xml: {e}")

    print("--- FIM DO TESTE DE CRASH ---")

if __name__ == "__main__":
    test_crash()
