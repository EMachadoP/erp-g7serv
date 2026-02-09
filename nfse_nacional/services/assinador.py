import os
import re
import base64
import binascii
import subprocess
import tempfile
from pathlib import Path
from lxml import etree
from signxml import XMLSigner, methods
from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import UnsupportedAlgorithm

def decode_pfx_base64(b64: str) -> bytes:
    if not b64:
        return b""

    # remove prefixos tipo data:application/x-pkcs12;base64,
    b64 = re.sub(r"^data:.*?;base64,", "", b64.strip(), flags=re.IGNORECASE)

    # remove espaços/quebras de linha
    b64 = re.sub(r"\s+", "", b64)

    # base64 urlsafe -> normal
    b64 = b64.replace("-", "+").replace("_", "/")

    # padding
    missing = len(b64) % 4
    if missing:
        b64 += "=" * (4 - missing)

    return base64.b64decode(b64)

def normalize_password(senha):
    if senha is None:
        return None

    if isinstance(senha, (bytes, bytearray)):
        return bytes(senha) if len(senha) > 0 else None

    s = str(senha)

    # remove \r\n do fim e aspas acidentais
    s = s.strip().strip('"').strip("'")

    return s.encode("utf-8") if s != "" else None

def diagnosticar_pfx_com_openssl(pfx_bytes: bytes, senha: str):
    """
    Roda openssl pkcs12 via subprocess para diferenciar senha errada de legado.
    Retorna dict com resultados.
    """
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "cert.pfx"
        p.write_bytes(pfx_bytes)

        def run(args):
            # timeout de 5s para não travar
            try:
                r = subprocess.run(args, capture_output=True, text=True, timeout=5)
                return r.returncode, (r.stdout or "")[-500:], (r.stderr or "")[-500:]
            except subprocess.TimeoutExpired:
                return -1, "TIMEOUT", "TIMEOUT"
            except FileNotFoundError:
                return -2, "OpenSSL não encontrado", ""

        # teste normal
        norm_pwd = senha
        if isinstance(senha, bytes):
            norm_pwd = senha.decode('utf-8', errors='ignore')
            
        code1, out1, err1 = run(["openssl", "pkcs12", "-info", "-in", str(p), "-noout", "-passin", f"pass:{norm_pwd}"])

        # teste legacy
        code2, out2, err2 = run(["openssl", "pkcs12", "-legacy", "-info", "-in", str(p), "-noout", "-passin", f"pass:{norm_pwd}"])

        return {
            "openssl_normal_ok": code1 == 0,
            "openssl_legacy_ok": code2 == 0,
            "normal_code": code1,
            "legacy_code": code2,
            "normal_err": err1,
            "legacy_err": err2,
        }

def carregar_certificado(caminho_ou_bytes, senha):
    # 1) Ler bytes
    if isinstance(caminho_ou_bytes, str):
        with open(caminho_ou_bytes, "rb") as f:
            pfx_data = f.read()
    else:
        pfx_data = caminho_ou_bytes or b""

    # Tentativa de decode robusto se parecer b64 string
    if isinstance(pfx_data, str):
         pfx_data = decode_pfx_base64(pfx_data)
    
    if not pfx_data:
        raise ValueError("Dados do certificado PFX nulos ou vazios.")
        
    # Se ainda vier bytes que parecem b64 (ex: lido de arquivo b64)
    if pfx_data[:2] in (b"MI", b"LS") and not (len(pfx_data) >= 2 and pfx_data[0] == 0x30):
         try:
             clean = re.sub(br"\s+", b"", pfx_data)
             pfx_data = base64.b64decode(clean, validate=True)
         except:
             pass

    header_hex = pfx_data[:4].hex()

    # 3) Normalizar senha
    senha_bytes = normalize_password(senha)

    # 4) Tentar carregar
    try:
        private_key, certificate, chain = pkcs12.load_key_and_certificates(pfx_data, senha_bytes)
    except UnsupportedAlgorithm as e:
         raise ValueError(
            "O PFX usa criptografia legada (ex.: RC2/3DES). O OpenSSL 3 bloqueou. "
            "Configure OPENSSL_CONF='/app/openssl.cnf' no Railway."
            f" (len={len(pfx_data)}, header={header_hex})"
        ) from e
    except ValueError as e:
        # Se falhou, vamos dar uma dica baseada na exceção
        msg_original = str(e)
        if "Invalid password" in msg_original or "mac verify failure" in msg_original:
             # Pode ser senha errada OU legado disfarçado
             raise ValueError(
                f"Falha ao carregar PFX: {msg_original}. \n"
                f"Dica: Se a senha estiver correta, isso é QUASE CERTEZA problema de PFX Legado no Linux. "
                f"Use a ferramenta de diagnóstico para confirmar 'openssl -legacy'. "
                f"(Header: {header_hex})"
             ) from e
        raise

    if private_key is None or certificate is None:
        raise ValueError("PFX carregou, mas não retornou chave privada e/ou certificado (arquivo incompleto?).")

    return private_key, certificate  # chain ignorado por compatibilidade

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
