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

        # Tentar varias codificacoes de senha
        encodings_to_try = []
        
        # 1. String original (UTF-8 no Linux)
        encodings_to_try.append(("UTF-8", senha))
        
        # 2. Latin-1 / CP1252 (Comum no Windows)
        try:
            if isinstance(senha, str):
                latin_pwd = senha.encode('latin-1').decode('latin-1') # Ensure it is valid latin-1
                if latin_pwd != senha: # Only add if different (has special chars) or just add anyway
                     pass
                encodings_to_try.append(("Latin-1", senha.encode('latin-1').decode('latin-1')))
        except:
            pass # Senha tem chars que nao existem em latin-1
            
        # 0. Verificar Providers Carregados e integridade do arquivo
        import hashlib
        file_hash = hashlib.sha256(pfx_bytes).hexdigest()
        
        # Check providers
        try:
            r_prov = subprocess.run(["openssl", "list", "-providers"], capture_output=True, text=True, timeout=5)
            providers_output = r_prov.stdout
        except Exception as e:
            providers_output = f"Erro ao listar providers: {e}"

        final_results = {}
        
        # Prepare byte candidates
        byte_candidates = []
        
        # Helper to add permutations
        def add_permutations(label, b_pwd):
            byte_candidates.append((label, b_pwd))
            byte_candidates.append((label + " + \\n", b_pwd + b"\n"))
        
        # 1. UTF-8 (Standard Linux)
        try:
             if isinstance(senha, str):
                 add_permutations("UTF-8", senha.encode('utf-8'))
             else:
                 add_permutations("UTF-8 (Bytes)", senha)
        except Exception as e:
             byte_candidates.append(("UTF-8 Error", b""))

        # 2. Latin-1 (Standard Windows) 
        try:
            if isinstance(senha, str):
                add_permutations("Latin-1", senha.encode('latin-1'))
        except Exception as e:
            pass 

        # 3. UTF-16LE (Windows Internal) - TENTATIVA FINAL
        try:
            if isinstance(senha, str):
                # UTF-16 adds BOM or null bytes, common in Windows crypto APIs
                add_permutations("UTF-16LE", senha.encode('utf-16le'))
        except:
             pass

        # 4. CP850 (DOS/Legacy PT-BR)
        try:
            if isinstance(senha, str):
                add_permutations("CP850", senha.encode('cp850'))
        except:
             pass

        for name, pwd_bytes in byte_candidates:
            # teste normal
            try:
                # -passin stdin, text=False para enviar bytes crus
                r1 = subprocess.run(
                    ["openssl", "pkcs12", "-info", "-in", str(p), "-noout", "-passin", "stdin"],
                    input=pwd_bytes,
                    capture_output=True, 
                    text=False, 
                    timeout=5
                )
                # Decode output manually for display
                out1 = r1.stdout.decode('utf-8', errors='replace')
                err1 = r1.stderr.decode('utf-8', errors='replace')
                code1 = r1.returncode
            except Exception as e:
                code1, out1, err1 = -1, "", str(e)

            # teste legacy
            try:
                r2 = subprocess.run(
                    ["openssl", "pkcs12", "-legacy", "-info", "-in", str(p), "-noout", "-passin", "stdin"],
                    input=pwd_bytes,
                    capture_output=True, 
                    text=False, 
                    timeout=5
                )
                out2 = r2.stdout.decode('utf-8', errors='replace')
                err2 = r2.stderr.decode('utf-8', errors='replace')
                code2 = r2.returncode
            except Exception as e:
                code2, out2, err2 = -1, "", str(e)
            
            final_results[name] = {
                "openssl_normal_ok": code1 == 0,
                "openssl_legacy_ok": code2 == 0,
                "normal_err": err1,
                "legacy_err": err2
            }
            
            # Se funcionou, paramos
            if code1 == 0 or code2 == 0:
                break
        
        # Retorna o ultimo ou o que funcionou
        return {
             "file_sha256": file_hash,
             "openssl_providers": providers_output,
             "tried_encodings": [x[0] for x in byte_candidates],
             "last_result": final_results
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
    certs_pem = certificate.public_bytes(serialization.Encoding.PEM)
    
    # Namespaces
    NS_NFSE = 'http://www.sped.fazenda.gov.br/nfse'
    NS_DSIG = 'http://www.w3.org/2000/09/xmldsig#'
    
    # Load XML
    root = etree.fromstring(xml_string.encode('utf-8'))

    # Digital Signature Settings
    if usar_sha256:
        signature_algorithm = 'rsa-sha256'
        digest_algorithm = 'sha256'
    else:
        signature_algorithm = 'rsa-sha1'
        digest_algorithm = 'sha1'

    # Create Signer
    signer = XMLSigner(
        method=methods.enveloped,
        signature_algorithm=signature_algorithm,
        digest_algorithm=digest_algorithm,
        c14n_algorithm='http://www.w3.org/TR/2001/REC-xml-c14n-20010315'
    )

    # Find infDPS (National standard uses 'infDPS')
    inf_dps = root.find('.//{%s}infDPS' % NS_NFSE)
    reference_uri = None
    if inf_dps is not None:
        dps_id = inf_dps.get('Id')
        if dps_id:
            reference_uri = f"#{dps_id}"

    # Sign the document
    signed_root = signer.sign(
        root,
        key=private_key,
        cert=certs_pem,
        reference_uri=reference_uri
    )

    # --- RE-CONSTRUÇÃO RIGOROSA DE NAMESPACES (Core Fix for E6155) ---
    # Para resolver definitivamente o erro E6155 (Sefin), 
    # precisamos garantir que tags de negócio NÃO tenham prefixo e Signature TENHA 'ds'
    
    def copy_element_clean(old_el, ns_target, ns_dsig):
        qname = etree.QName(old_el)
        ns = qname.namespace
        ln = qname.localname
        
        # Define nsmap:
        # 1. No root (DPS), definimos o namespace padrão de negócio.
        # 2. No Signature, trocamos o namespace padrão para xmldsig (conforme exigência Sefin de zero prefixos).
        if ln == "DPS":
            new_nsmap = {None: ns_target}
        elif ln == "Signature":
            new_nsmap = {None: ns_dsig}
        else:
            new_nsmap = None # Herda do pai
            
        # Define a nova tag usando o namespace correspondente.
        # Como o None prefix está mapeado no nsmap local ou herdado,
        # o lxml gerará as tags sem prefixo (ex: <Signature xmlns="...">).
        if ns == ns_target:
            tag = "{%s}%s" % (ns_target, ln)
        elif ns == ns_dsig:
            tag = "{%s}%s" % (ns_dsig, ln)
        else:
            tag = old_el.tag
            
        new_el = etree.Element(tag, nsmap=new_nsmap)
        new_el.text = old_el.text
        new_el.tail = old_el.tail
        
        # Copiar atributos (Removendo prefixos de Ids etc.)
        for k, v in old_el.attrib.items():
            aq = etree.QName(k)
            new_el.set(aq.localname, v)
            
        # Copiar filhos recursivamente
        for child in old_el:
            if isinstance(child, etree._Element):
                new_el.append(copy_element_clean(child, ns_target, ns_dsig))
                
        return new_el

    # Re-gera o documento inteiro a partir da raiz limpa
    # signed_root é o elemento <DPS> retornado pelo signxml
    definitive_root = copy_element_clean(signed_root, NS_NFSE, NS_DSIG)

    # Double check for redundant declarations
    etree.cleanup_namespaces(definitive_root)

    # Gera string XML final
    xml_output = etree.tostring(definitive_root, encoding='UTF-8', xml_declaration=False).decode('utf-8')
    
    # Prepend declaration manualmente com aspas duplas e sem newline se possivel
    # A Sefin pode ser chata com aspas simples ou espaços extras
    header = '<?xml version="1.0" encoding="UTF-8"?>'
    return header + xml_output
