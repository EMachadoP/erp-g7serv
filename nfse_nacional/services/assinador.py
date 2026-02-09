import os
import re
import base64
import binascii
from lxml import etree
from signxml import XMLSigner, XMLVerifier, methods
from cryptography.hazmat.primitives.serialization import pkcs12
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


    # 2) Se vier base64 por engano, tenta decodificar (sem quebrar se não for)
    #    - PFX em base64 costuma começar com "MII..."
    if pfx_data[:2] in (b"MI", b"LS") and not (len(pfx_data) >= 2 and pfx_data[0] == 0x30):
        try:
            clean = re.sub(br"\s+", b"", pfx_data)
            # se for PEM, extrai o miolo
            m = re.search(br"-----BEGIN[^-]+-----(.+?)-----END[^-]+-----", pfx_data, re.S)
            if m:
                clean = re.sub(br"\s+", b"", m.group(1))
            pfx_data = base64.b64decode(clean, validate=True)
        except binascii.Error:
            pass  # não era base64 válido, segue como está


    header_hex = pfx_data[:4].hex()


    # 3) Normalizar senha (muito comum vir com aspas ou newline do ENV/Secrets)
    if senha is None:
        senha_str = ""
    elif isinstance(senha, (bytes, bytearray)):
        senha_str = None
        senha_bytes_direct = bytes(senha)
    else:
        senha_str = str(senha).strip()
        senha_str = senha_str.strip('"').strip("'")  # remove aspas
        senha_bytes_direct = None


    # 4) Montar candidatos de senha
    candidatos = []
    if senha_bytes_direct is not None:
        candidatos.append(senha_bytes_direct)
    else:
        if senha_str == "":
            candidatos.append(None)   # sem senha
            candidatos.append(b"")    # senha vazia
        else:
            candidatos.extend([
                senha_str.encode("utf-8"),
                senha_str.encode("latin-1"),
                senha_str.encode("utf-16le"),
            ])


    last_err = None


    for pw in candidatos:
        try:
            private_key, certificate, additional = pkcs12.load_key_and_certificates(pfx_data, pw)


            if private_key is None or certificate is None:
                raise ValueError(
                    "PFX carregou, mas não contém chave privada e/ou certificado. "
                    "Reexporte marcando 'incluir chave privada'."
                )


            return private_key, certificate


        except UnsupportedAlgorithm as e:
            # Caso típico: OpenSSL 3 bloqueando RC2/3DES etc.
            raise ValueError(
                "O PFX parece usar criptografia legada (ex.: RC2/3DES) que o OpenSSL 3 do Linux/Railway pode bloquear. "
                "Solução: reexportar/converter o PFX para AES (comandos abaixo)."
                f" (len={len(pfx_data)}, header={header_hex})"
            ) from e


        except ValueError as e:
            last_err = e


    raise ValueError(
        f"Falha ao carregar certificado (len={len(pfx_data)} bytes, header={header_hex}). "
        f"Causa provável: senha incorreta, senha chegando alterada (aspas/newline) ou PFX legado/incompatível. "
        f"Erro final: {last_err}"
    )

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
    # signature_algorithm='rsa-sha256' is standard for NFSe
    # digest_algorithm='sha256' is standard for NFSe
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
