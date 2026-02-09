import requests
import tempfile
import os
import gzip
import base64
import json
from cryptography.hazmat.primitives import serialization
from .xml_builder import renderizar_xml_dps
from .assinador import assinar_xml, carregar_certificado
from nfse_nacional.models import NFSe

class NFSeNacionalClient:
    URL_PRODUCAO = "https://sefin.nfse.gov.br/sefinnacional/nfse"
    URL_HOMOLOGACAO = "https://sefin.producaorestrita.nfse.gov.br/SefinNacional/nfse"

    def enviar_dps(self, nfse_obj: NFSe):
        """
        Gera o XML, assina e envia para a API Nacional.
        """
        try:
            # Determine URL based on environment
            # 1 = Produção, 2 = Homologação
            if nfse_obj.empresa.ambiente == 1:
                api_url = self.URL_PRODUCAO
            else:
                api_url = self.URL_HOMOLOGACAO

            # 1. Gerar XML
            xml_content = renderizar_xml_dps(nfse_obj)
            
            # Save generated XML for debugging
            nfse_obj.xml_envio = xml_content
            nfse_obj.save()
            
            # 2. Ler Certificado (Bytes)
            # Evita usar .path que pode não existir em ambientes de nuvem (Railway/Heroku/AWS)
            try:
                if nfse_obj.empresa.certificado_a1:
                    with nfse_obj.empresa.certificado_a1.open("rb") as f:
                        cert_bytes = f.read()
                else:
                     raise ValueError("Arquivo de certificado não encontrado.")
            except Exception as e:
                # Fallback to path if open fails (unlikely if field exists)
                if hasattr(nfse_obj.empresa.certificado_a1, 'path'):
                     with open(nfse_obj.empresa.certificado_a1.path, 'rb') as f:
                        cert_bytes = f.read()
                else:
                    raise e

            cert_password = nfse_obj.empresa.senha_certificado
            
            # 3. Assinar XML
            signed_xml = assinar_xml(xml_content, cert_bytes, cert_password)
            
            # 4. Preparar mTLS (Certificado e Chave para a requisição)
            private_key, certificate = carregar_certificado(cert_bytes, cert_password)
            
            # Escrever chave e certificado em arquivos temporários para o requests
            with tempfile.NamedTemporaryFile(delete=False) as key_file, \
                 tempfile.NamedTemporaryFile(delete=False) as cert_file:
                
                # Write Private Key
                key_bytes = private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption()
                )
                key_file.write(key_bytes)
                key_file.flush()
                
                # Write Certificate
                cert_bytes = certificate.public_bytes(serialization.Encoding.PEM)
                cert_file.write(cert_bytes)
                cert_file.flush()
                
                key_path = key_file.name
                cert_path_temp = cert_file.name

            try:
                # 4. Enviar para a API
                # Protocolo: GZIP -> Base64 -> JSON
                
                # Compress with GZIP
                # signed_xml is a string, encode to bytes
                signed_xml_bytes = signed_xml.encode('utf-8')
                gzipped_xml = gzip.compress(signed_xml_bytes)
                
                # Encode to Base64
                b64_xml = base64.b64encode(gzipped_xml).decode('utf-8')
                
                # Create JSON payload
                payload = {
                    "dpsXmlGZipB64": b64_xml
                }
                
                print(f"--- TENTANDO ENVIO PARA: {api_url} ---")
                headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
                print(f"--- HEADER: {headers} ---")
                
                response = requests.post(
                    api_url,
                    json=payload,
                    headers=headers,
                    cert=(cert_path_temp, key_path),
                    timeout=30
                )
                
                # 5. Processar Resposta
                if response.status_code in (200, 201):
                    data = response.json()
                    
                    # Check for business errors (if 'erros' key exists and is not empty)
                    if 'erros' in data and data['erros']:
                        nfse_obj.status = 'Rejeitada'
                        nfse_obj.xml_envio = signed_xml
                        nfse_obj.json_erro = data
                        nfse_obj.save()
                        return False, f"Erro de negócio NFS-e: {data['erros']}"

                    # Success
                    nfse_obj.status = 'Autorizada'
                    nfse_obj.xml_envio = signed_xml
                    nfse_obj.xml_retorno = response.text
                    
                    # Extract fields
                    nfse_obj.chave_acesso = data.get('chaveAcesso')
                    # nfse_obj.numero_nfse = data.get('idDps') # Field does not exist yet
                    
                    # Decompress XML to store the full NFS-e
                    xml_gzip_b64 = data.get('nfseXmlGZipB64')
                    if xml_gzip_b64:
                        try:
                            xml_bytes = gzip.decompress(base64.b64decode(xml_gzip_b64))
                            nfse_obj.xml_retorno = xml_bytes.decode('utf-8')
                        except Exception as e:
                            print(f"Erro ao descompactar XML de retorno: {e}")
                            nfse_obj.xml_retorno = response.text # Fallback

                    nfse_obj.save()
                    return True, "NFS-e Autorizada com sucesso."
                else:
                    nfse_obj.status = 'Rejeitada'
                    nfse_obj.xml_envio = signed_xml
                    nfse_obj.json_erro = {
                        'status_code': response.status_code,
                        'response': response.text
                    }
                    nfse_obj.save()
                    return False, f"Erro na API: {response.status_code} - {response.text}"

            finally:
                # Limpar arquivos temporários
                if os.path.exists(key_path):
                    os.unlink(key_path)
                if os.path.exists(cert_path_temp):
                    os.unlink(cert_path_temp)

        except Exception as e:
            nfse_obj.status = 'Rejeitada'
            nfse_obj.json_erro = {'exception': str(e)}
            nfse_obj.save()
            return False, f"Erro interno: {str(e)}"
