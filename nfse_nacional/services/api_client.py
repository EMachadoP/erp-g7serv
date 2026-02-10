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
    URL_PRODUCAO = "https://sefin.nfse.gov.br/SefinNacional/nfse"
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
            try:
                if nfse_obj.empresa.certificado_base64:
                    import base64
                    cert_bytes = base64.b64decode(nfse_obj.empresa.certificado_base64)
                elif nfse_obj.empresa.certificado_a1:
                     # Fallback to file opening (might fail on Railway if file is gone)
                    with nfse_obj.empresa.certificado_a1.open("rb") as f:
                        cert_bytes = f.read()
                else:
                     raise ValueError("Certificado não configurado.")
            except Exception as e:
                 # Last resort path attempt
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
                    "dpsXmlGzipB64": b64_xml
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
                    print(f"DEBUG NFSe: Resposta POST recebida. Chaves: {list(data.keys())}")
                    
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
                    
                    # Decompress XML to store the full NFS-e
                    xml_gzip_b64 = data.get('nfseXmlGZipB64')
                    if xml_gzip_b64:
                        try:
                            import gzip
                            xml_bytes = gzip.decompress(base64.b64decode(xml_gzip_b64))
                            nfse_obj.xml_retorno = xml_bytes.decode('utf-8')
                        except Exception as e:
                            print(f"Erro ao descompactar XML de retorno: {e}")
                            nfse_obj.xml_retorno = response.text # Fallback

                    # NOVO: Verifica se o PDF já veio na resposta da emissão
                    pdf_b64 = data.get('danfsePdfB64') or data.get('pdfB64') or data.get('danfsePdf')
                    if pdf_b64:
                        try:
                            nfse_obj.pdf_danfse = base64.b64decode(pdf_b64)
                            print("DEBUG NFSe: PDF encontrado na resposta da emissão!")
                        except:
                            pass

                    nfse_obj.save()
                    
                    # Após autorização, tenta baixar o DANFSe (PDF) se ainda não tiver
                    if nfse_obj.chave_acesso and not nfse_obj.pdf_danfse:
                        try:
                            self.baixar_danfse(nfse_obj, cert_path_temp, key_path)
                        except Exception as e:
                            print(f"Aviso: Não foi possível baixar DANFSe automaticamente: {e}")
                    
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

    def baixar_danfse(self, nfse_obj, cert_path=None, key_path=None):
        """
        Baixa o DANFSe (PDF) da API Nacional usando a chave de acesso.
        Endpoint: GET /nfse/{chaveAcesso}
        """
        if not nfse_obj.chave_acesso:
            raise ValueError("Chave de acesso não disponível para baixar DANFSe.")
        
        if nfse_obj.empresa.ambiente == 1:
            base_url = self.URL_PRODUCAO
        else:
            base_url = self.URL_HOMOLOGACAO
        
        url = f"{base_url}/{nfse_obj.chave_acesso}"
        print(f"DEBUG NFSe: Iniciando GET em {url}")
        
        # ... (código de certificado igual ao anterior até o try)
        # (Vou resumir para não estourar o limite de linhas do tool, mas mantendo a lógica de certificado)

        # Se cert_path e key_path não foram fornecidos, cria temporários
        temp_files = []
        if not cert_path or not key_path:
            # Reuso da lógica de criação de cert temporário
            try:
                if nfse_obj.empresa.certificado_base64:
                    cert_bytes_raw = base64.b64decode(nfse_obj.empresa.certificado_base64)
                elif nfse_obj.empresa.certificado_a1:
                    with nfse_obj.empresa.certificado_a1.open("rb") as f:
                        cert_bytes_raw = f.read()
                else:
                    raise ValueError("Certificado não configurado.")
            except Exception as e:
                if hasattr(nfse_obj.empresa.certificado_a1, 'path'):
                    with open(nfse_obj.empresa.certificado_a1.path, 'rb') as f:
                        cert_bytes_raw = f.read()
                else:
                    raise e
            
            from .assinador import carregar_certificado
            private_key, certificate = carregar_certificado(
                cert_bytes_raw, nfse_obj.empresa.senha_certificado
            )
            
            import tempfile
            key_file = tempfile.NamedTemporaryFile(delete=False)
            cert_file = tempfile.NamedTemporaryFile(delete=False)
            
            from cryptography.hazmat.primitives import serialization
            key_bytes = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            )
            key_file.write(key_bytes)
            key_file.flush()
            
            cert_bytes_pem = certificate.public_bytes(serialization.Encoding.PEM)
            cert_file.write(cert_bytes_pem)
            cert_file.flush()
            
            key_path = key_file.name
            cert_path = cert_file.name
            key_file.close()
            cert_file.close()
            temp_files = [key_path, cert_path]
        
        try:
            # Tenta baixar com Accept PDF
            headers = {
                'Accept': 'application/pdf, application/json'
            }
            
            response = requests.get(
                url,
                headers=headers,
                cert=(cert_path, key_path),
                timeout=30
            )
            
            print(f"DEBUG NFSe: Status GET: {response.status_code}")
            content_type = response.headers.get('Content-Type', '').lower()
            print(f"DEBUG NFSe: Content-Type GET: {content_type}")
            
            if response.status_code == 200:
                if 'pdf' in content_type:
                    nfse_obj.pdf_danfse = response.content
                    nfse_obj.save(update_fields=['pdf_danfse'])
                    print(f"DEBUG NFSe: PDF binário baixado ({len(response.content)} bytes)")
                    return True
                elif 'json' in content_type:
                    data = response.json()
                    print(f"DEBUG NFSe: Resposta GET é JSON. Chaves: {list(data.keys())}")
                    # Tenta extrair PDF do JSON
                    pdf_b64 = data.get('danfsePdfB64') or data.get('pdfB64') or data.get('danfsePdf')
                    if pdf_b64:
                        nfse_obj.pdf_danfse = base64.b64decode(pdf_b64)
                        nfse_obj.save(update_fields=['pdf_danfse'])
                        print(f"DEBUG NFSe: PDF extraído do JSON ({len(nfse_obj.pdf_danfse)} bytes)")
                        return True
                    
                    # Se não tem PDF mas tem XML, atualiza o XML retorno se estiver vazio
                    xml_b64 = data.get('xmlB64') or data.get('nfseXmlGZipB64')
                    if xml_b64 and not nfse_obj.xml_retorno:
                         try:
                             if data.get('nfseXmlGZipB64'):
                                 import gzip
                                 nfse_obj.xml_retorno = gzip.decompress(base64.b64decode(xml_b64)).decode('utf-8')
                             else:
                                 nfse_obj.xml_retorno = base64.b64decode(xml_b64).decode('utf-8')
                             nfse_obj.save(update_fields=['xml_retorno'])
                         except:
                             pass

            print(f"DEBUG NFSe: Falha ao obter PDF (Status {response.status_code})")
            
            # Tenta construir link para consulta pública se ainda não tiver e se falhou o PDF
            if not nfse_obj.link_danfse:
                link = f"https://www.nfse.gov.br/ConsultaPublica/?chave={nfse_obj.chave_acesso}"
                nfse_obj.link_danfse = link
                nfse_obj.save(update_fields=['link_danfse'])
            
            return False
            
        finally:
            for f in temp_files:
                if os.path.exists(f):
                    os.unlink(f)
