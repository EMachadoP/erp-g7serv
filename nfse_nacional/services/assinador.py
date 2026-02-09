import os
import re
import base64
import binascii
from lxml import etree
from signxml import XMLSigner, methods
from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import UnsupportedAlgorithm

def carregar_certificado(caminho_ou_bytes, senha):
    # 1) Ler bytes
    if isinstance(caminho_ou_bytes, str):
        with open(caminho_ou_bytes, "rb") as f:
            pfx_data = f.read()
    else:
        pfx_data = caminho_ou_bytes or b""

    if not pfx_data:
        raise ValueError("Dados do certificado PFX nulos ou vazios.")

    # 2) Se vier base64 por engano, tenta decodificar
    if pfx_data[:2] in (b"MI", b"LS") and not (len(pfx_data) >= 2 and pfx_data[0] == 0x30):
        try:
            clean = re.sub(br"\s+", b"", pfx_data)
            m = re.search(br"-----BEGIN[^-]+-----(.+?)-----END[^-]+-----", pfx_data, re.S)
            if m:
                clean = re.sub(br"\s+", b"", m.group(1))
            pfx_data = base64.b64decode(clean, validate=True)
        except binascii.Error:
            pass 

    header_hex = pfx_data[:4].hex()

    # 3) Normalizar senha
    if senha is None:
        senha_bytes = None
    elif isinstance(senha, (bytes, bytearray)):
        senha_bytes = bytes(senha) if len(senha) > 0 else None
    else:
        senha_str = str(senha)
        senha_str = senha_str.strip()
        senha_bytes = senha_str.encode("utf-8") if senha_str != "" else None

    # 4) Tentar carregar
    try:
        private_key, certificate, chain = pkcs12.load_key_and_certificates(pfx_data, senha_bytes)
    except UnsupportedAlgorithm as e:
         raise ValueError(
            "O PFX parece usar criptografia legada (ex.: RC2/3DES) que o OpenSSL 3 do Linux/Railway bloqueia. "
            "Solução: Habilitar 'legacy provider' no OpenSSL ou reexportar o certificado como AES."
            f" (len={len(pfx_data)}, header={header_hex})"
        ) from e
    except ValueError as e:
        last_err = e
        # Tentativa de fallback de encoding de senha se falhar (ex: latin-1)
        if senha_bytes:
             try:
                 senha_latin = str(senha).strip().encode('latin-1')
                 private_key, certificate, chain = pkcs12.load_key_and_certificates(pfx_data, senha_latin)
             except:
                 raise ValueError(
                    f"Falha ao carregar PFX (len={len(pfx_data)}, header={header_hex}). "
                    f"Erro: {last_err}"
                ) from e
        else:
             raise ValueError(
                f"Falha ao carregar PFX (len={len(pfx_data)}, header={header_hex}). "
                f"Erro: {last_err}"
            ) from e

    if private_key is None or certificate is None:
        raise ValueError("PFX carregou, mas não retornou chave privada e/ou certificado (arquivo incompleto?).")

    return private_key, certificate  # Mantendo retorno de 2 valores por compatibilidade com resto do codigo

def montar_cadeia_pem(cert, chain):
    pem = cert.public_bytes(serialization.Encoding.PEM)
    if chain:
        for c in chain:
            pem += c.public_bytes(serialization.Encoding.PEM)
    return pem

def assinar_xml(xml_string, caminho_ou_bytes_pfx, senha, usar_sha256=True):
    """
    Assina o XML da DPS usando o certificado A1 (.pfx).
    """
    # Load Key and Cert
    # carregar_certificado returns (private_key, certificate) - we adapted to ignore chain for compat
    # Re-reading to get chain if needed? 
    # Let's adapt carregar_certificado to ignore chain for now or update callers.
    # The snippet used 'carregar_certificado' returning 3 values.
    # My existing code expects 2. I kept 2 in the return above.
    
    private_key, certificate = carregar_certificado(caminho_ou_bytes_pfx, senha)
    # chain is missing in this call, but we can reconstruct pem 
    
    certs_pem = certificate.public_bytes(serialization.Encoding.PEM)
    # If we need chain, we should update carregar_certificado to return it.
    
    root = etree.fromstring(xml_string.encode('utf-8'))

    if usar_sha256:
        signature_algorithm = 'rsa-sha256'
        digest_algorithm = 'sha256'
    else:
        signature_algorithm = 'rsa-sha1'
        digest_algorithm = 'sha1'

    signer = XMLSigner(
        method=methods.enveloped,
        signature_algorithm=signature_algorithm,
        digest_algorithm=digest_algorithm,
        c14n_algorithm='http://www.w3.org/TR/2001/REC-xml-c14n-20010315'
    )

    # Check for 'InfDPS' to sign specifically that element if present
    # national standard usually signs the InfDPS
    inf_dps = root.find('.//{http://www.abrasf.org.br/nfse.xsd}InfDPS')
    reference_uri = None
    node_to_sign = root
    
    if inf_dps is not None:
        # If InfDPS exists, we might want to sign IT, but verify if signature should be child of root or InfDPS.
        # Enveloped signature usually goes as a sibling of the content or inside the root.
        # If we sign 'root', it signs the whole doc.
        # If we sign 'inf_dps', the signature usually wraps it or is appended.
        # For NFSe Nacional, usually the signature is an element of the 'DPS' (root?) or sends 'DPS' which contains 'InfDPS' and 'Signature'.
        
        # Checking 'Id' attribute
        dps_id = inf_dps.get('Id')
        if dps_id:
             reference_uri = f"#{dps_id}"

    signed_root = signer.sign(
        root,
        key=private_key,
        cert=certs_pem,
        reference_uri=reference_uri # If None, signs the root object referenced by empty URI? or whole doc?
    )

    return etree.tostring(signed_root, encoding='UTF-8', xml_declaration=True).decode('utf-8')
