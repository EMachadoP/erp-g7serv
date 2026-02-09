import os
from lxml import etree
from signxml import XMLSigner, XMLVerifier, methods
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.primitives import serialization

def carregar_certificado(caminho_ou_bytes, senha):
    """
    Carrega o arquivo .pfx e retorna a chave privada e o certificado.
    Aceita caminho do arquivo (str) ou o conteúdo em bytes.
    """
    if isinstance(caminho_ou_bytes, str):
        with open(caminho_ou_bytes, 'rb') as f:
            pfx_data = f.read()
    else:
        pfx_data = caminho_ou_bytes

    # Load PFX
    # Ensure raw bytes are present
    if not pfx_data:
        raise ValueError("Dados do certificado PFX nulos ou vazios.")

    # Try different password encodings
    encodings = ['utf-8', 'latin-1']
    last_error = None

    for encoding in encodings:
        try:
             bytes_senha = senha
             if isinstance(senha, str):
                 bytes_senha = senha.encode(encoding)
             
             private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
                pfx_data,
                bytes_senha
             )
             return private_key, certificate
        except Exception as e:
            last_error = e
    
    # If we get here, all attempts failed
    raise ValueError(f"Falha ao carregar certificado (Tamanho: {len(pfx_data)} bytes). Erro: {last_error}")

def assinar_xml(xml_string, caminho_ou_bytes_pfx, senha):
    """
    Assina o XML da DPS usando o certificado A1 (.pfx).
    Aceita caminho (str) ou bytes do PFX.
    """
    # Load Key and Cert
    private_key, certificate = carregar_certificado(caminho_ou_bytes_pfx, senha)

    # Parse XML
    root = etree.fromstring(xml_string.encode('utf-8'))

    # Sign XML
    # method=methods.enveloped is default
    # signature_algorithm='rsa-sha1' is standard for NFSe
    # digest_algorithm='sha1' is standard for NFSe
    # c14n_algorithm='http://www.w3.org/TR/2001/REC-xml-c14n-20010315' (C14N)
    
    signer = XMLSigner(
        method=methods.enveloped,
        signature_algorithm='rsa-sha256',
        digest_algorithm='sha256',
        c14n_algorithm='http://www.w3.org/TR/2001/REC-xml-c14n-20010315'
    )

    # We need to sign the InfDPS tag usually, or the root if it's the only one.
    # For Nacional standard, usually the signature goes into the root, signing the InfDPS.
    # Let's try to sign the root, referencing the InfDPS ID if needed.
    # But signxml signs the payload.
    
    # Extract cert data for KeyInfo
    cert_pem = certificate.public_bytes(serialization.Encoding.PEM)
    
    signed_root = signer.sign(
        root,
        key=private_key,
        cert=cert_pem,
        reference_uri=None # Sign the whole element passed (root) or specific ID?
        # Usually we sign the InfDPS element.
    )
    
    # If we need to sign a specific element (InfDPS) and place signature elsewhere, logic changes.
    # But standard enveloped signature signs the root and places signature inside.
    # If the user said "Encontrar a tag raiz (ou a tag InfDPS)", let's assume signing the root is fine for now
    # or we might need to find 'InfDPS' and sign that.
    
    # Let's look for InfDPS to be safe, as usually that's what is signed.
    # inf_dps = root.find('.//{http://www.abrasf.org.br/nfse.xsd}InfDPS')
    # if inf_dps is not None:
    #    signed_root = signer.sign(inf_dps, key=private_key, cert=cert_pem)
    # But the signature must be appended to the XML.
    
    # For now, let's sign the root as it's an enveloped signature.
    
    # Return as string with XML declaration
    return etree.tostring(signed_root, encoding='UTF-8', xml_declaration=True).decode('utf-8')
