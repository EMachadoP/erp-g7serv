import requests
import base64
import os
import tempfile
import logging
from django.conf import settings

from django.conf import settings
from core.models import CompanySettings

logger = logging.getLogger(__name__)

class CoraService:
    def __init__(self):
        # 1. Try to get from Database
        db_settings = CompanySettings.objects.first()
        
        # UI/Stage Settings
        self.base_url = getattr(settings, 'CORA_API_URL', "https://api.stage.cora.com.br/v2")
        self.auth_url = getattr(settings, 'CORA_AUTH_URL', "https://matls-auth.stage.cora.com.br/token")
        
        # Client ID Priority: DB -> Settings -> ENV
        self.client_id = (db_settings.cora_client_id if db_settings else None) or \
                         getattr(settings, 'CORA_CLIENT_ID', os.getenv('CORA_CLIENT_ID'))
        
        # Cora Certificates Priority: DB (Base64) -> ENV
        cora_cert_b64 = (db_settings.cora_cert_base64 if db_settings else None) or os.getenv('CORA_CERT_BASE64')
        cora_key_b64 = (db_settings.cora_key_base64 if db_settings else None) or os.getenv('CORA_KEY_BASE64')
        
        if not cora_cert_b64 or not cora_key_b64:
            self.cert_pair = None
            logger.error("Cora mTLS certificates (CORA_CERT_BASE64/CORA_KEY_BASE64) not found in environment.")
            return

        # Create temporary files for the certificate and key (requirement for 'requests')
        try:
            self.cert_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pem')
            self.key_file = tempfile.NamedTemporaryFile(delete=False, suffix='.key')
            
            self.cert_file.write(base64.b64decode(cora_cert_b64))
            self.key_file.write(base64.b64decode(cora_key_b64))
            
            self.cert_file.close()
            self.key_file.close()
            
            # The certificate pair for mTLS
            self.cert_pair = (self.cert_file.name, self.key_file.name)
        except Exception as e:
            self.cert_pair = None
            logger.error(f"Failed to process Cora certificates: {e}")

    def obter_token(self):
        """
        Direct Integration Step: Exchange certificate for Access Token
        """
        if not self.cert_pair or not self.client_id:
            logger.error("Cannot obtain token: Missing certificates or client_id.")
            return None
            
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id
        }
        
        try:
            response = requests.post(
                self.auth_url, 
                data=payload, 
                cert=self.cert_pair, # mTLS Magic
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json().get("access_token")
            
            logger.error(f"Cora Auth Error ({response.status_code}): {response.text}")
        except Exception as e:
            logger.error(f"Cora Auth Exception: {e}")
            
        return None

    def gerar_fatura(self, fatura_data):
        """
        Sends the invoice data to Cora API.
        Expected amount in 'fatura_data' should already be in cents (integer).
        """
        token = self.obter_token()
        if not token:
            return {"erro": "Falha na autenticação mTLS"}

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/invoices/", 
                json=fatura_data, 
                headers=headers,
                cert=self.cert_pair,
                timeout=15
            )
            
            return response.json()
        except Exception as e:
            logger.error(f"Cora Invoice Generation Exception: {e}")
            return {"erro": str(e)}

    def __del__(self):
        # Cleanup temporary files safely
        try:
            if hasattr(self, 'cert_file') and os.path.exists(self.cert_file.name):
                os.unlink(self.cert_file.name)
            if hasattr(self, 'key_file') and os.path.exists(self.key_file.name):
                os.unlink(self.key_file.name)
        except:
            pass
