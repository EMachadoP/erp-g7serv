import requests
import tempfile
import os
from django.utils import timezone
from datetime import timedelta
from cryptography.hazmat.primitives import serialization
from integracao_cora.models import CoraConfig
from nfse_nacional.models import Empresa
from nfse_nacional.services.assinador import carregar_certificado

class CoraAuth:
    URL_PRODUCAO = "https://matls-clients.api.cora.com.br/token"
    URL_HOMOLOGACAO = "https://matls-clients.api.stage.cora.com.br/token"

    def get_access_token(self):
        """
        Retorna um access_token válido.
        Se o atual estiver expirado ou inexistente, solicita um novo.
        """
        config = CoraConfig.objects.first()
        if not config:
            raise Exception("Configuração da Cora não encontrada.")

        # Check if token is valid (with a 5-minute buffer)
        if config.access_token and config.token_expires_at:
            if config.token_expires_at > timezone.now() + timedelta(minutes=5):
                return config.access_token

        # Request new token
        return self._request_new_token(config)

    def _request_new_token(self, config):
        """
        Solicita um novo token à API da Cora usando mTLS.
        """
        from integracao_cora.services.base import mTLS_cert_paths

        with mTLS_cert_paths() as cert_files:
            # Determine URL
            url = self.URL_PRODUCAO if config.ambiente == 1 else self.URL_HOMOLOGACAO

            # Preparar credenciais limpando espaços
            client_id = config.client_id.strip() if config.client_id else ""
            client_secret = config.client_secret.strip() if config.client_secret else ""

            # Payload (apenas grant_type, id/secret podem ir no header via Basic Auth)
            # No entanto, a Cora aceita ambos. Vou mandar grant_type e client_id no body
            # e usar auth=(id, secret) que gera o header Authorization: Basic.
            payload = {
                'grant_type': 'client_credentials',
                'client_id': client_id  # Mantém no body por precaução/compatibilidade
            }
            
            # Headers explícitos
            headers = {
                'Accept': 'application/json'
            }

            # Request usando Basic Auth + mTLS
            try:
                response = requests.post(
                    url,
                    data=payload,
                    auth=(client_id, client_secret),
                    headers=headers,
                    cert=cert_files,
                    timeout=30
                )
            except Exception as e:
                raise Exception(f"Falha na requisição de rede para Cora: {str(e)}")

            if response.status_code != 200:
                error_msg = response.text
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error_description') or error_data.get('error') or response.text
                except:
                    pass
                
                # Ajuda o usuário a identificar o problema
                if "invalid_client" in str(error_msg).lower():
                    error_msg = "invalid_client (Verifique se o Client ID e Ambiente estão corretos e se o certificado é válido)"
                
                raise Exception(f"Erro ao autenticar na Cora: {response.status_code} - {error_msg}")

            data = response.json()
            
            # Save new token
            config.access_token = data['access_token']
            expires_in = data.get('expires_in', 3600) # Default 1 hour
            config.token_expires_at = timezone.now() + timedelta(seconds=expires_in)
            config.save()

            return config.access_token
