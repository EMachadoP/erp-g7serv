import re
import os

path = r'nfse_nacional/services/api_client.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Reconstruct the missing blocks for enviar_dps and outdent baixar_danfse
new_content = re.sub(
    r'                    return True, "NFS-e Autorizada com sucesso\."[\s\n]+def baixar_danfse',
    r'''                    return True, "NFS-e Autorizada com sucesso."
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

    def baixar_danfse''',
    content,
    flags=re.MULTILINE
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(new_content)
print("File fixed with script.")
