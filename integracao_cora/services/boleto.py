import requests
import json
import uuid
from django.utils import timezone
from integracao_cora.models import CoraConfig, BoletoCora
from integracao_cora.services.auth import CoraAuth
from integracao_cora.services.base import mTLS_cert_paths

class CoraBoleto:
    URL_PRODUCAO = "https://matls-clients.api.cora.com.br/v2/invoices"
    URL_HOMOLOGACAO = "https://matls-clients.api.stage.cora.com.br/v2/invoices"

    def gerar_boleto(self, nfse_obj):
        """
        Gera um boleto na Cora para a NFS-e fornecida.
        """
        # 1. Get Access Token
        auth = CoraAuth()
        access_token = auth.get_access_token()

        # 2. Prepare Payload
        config = CoraConfig.objects.first()
        url = self.URL_PRODUCAO if config.ambiente == 1 else self.URL_HOMOLOGACAO

        # Clean Customer Data
        customer_name = nfse_obj.cliente.name[:60]
        customer_document = nfse_obj.cliente.document.replace('.', '').replace('-', '').replace('/', '')
        
        # Determine Identity Type
        identity_type = 'CNPJ' if len(customer_document) > 11 else 'CPF'

        # 2b. Load Billing Configs
        fine_amount_cents = 0
        interest_rate = 0
        if config:
            # Fine: amount in cents
            fine_amount_cents = int(float(nfse_obj.servico.sale_price) * (float(config.taxa_multa) / 100) * 100)
            # Interest: rate (decimal/percentage)
            interest_rate = float(config.taxa_juros)
            instrucoes = config.instrucoes_boleto or ""
        else:
            instrucoes = ""

        # Calculate Due Date (Assuming +5 days if not specified)
        due_date = (timezone.now() + timezone.timedelta(days=5)).strftime('%Y-%m-%d')
        
        # Payload Structure for V2
        payload = {
            "code": str(nfse_obj.numero_dps), # Unique code for the invoice in client's system
            "customer": {
                "name": customer_name,
                "document": {
                    "identity": customer_document,
                    "type": identity_type
                },
            },
            "services": [
                {
                    "name": nfse_obj.servico.name[:255],
                    "description": instrucoes[:1000],
                    "amount": int(nfse_obj.servico.sale_price * 100) # Amount in cents
                }
            ],
            "payment_terms": {
                "due_date": due_date,
                "fine": {
                    "date": due_date,
                    "amount": fine_amount_cents
                },
                "interest": {
                    "date": due_date,
                    "rate": interest_rate
                }
            },
            "payment_forms": [
                "BANK_SLIP",
                "PIX"
            ]
        }

        # 3. Send Request with mTLS + Bearer Token
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'Idempotency-Key': str(uuid.uuid4()) # Unique key
        }

        with mTLS_cert_paths() as cert_files:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                cert=cert_files,
                timeout=30
            )

            if response.status_code not in (200, 201):
                raise Exception(f"Erro ao gerar boleto Cora: {response.status_code} - {response.text}")

            data = response.json()
            
            # 4. Save BoletoCora
            # Response structure usually has 'id', 'payment_options' -> 'bank_slip' -> 'barcode', 'digitable', 'url'
            # Let's inspect typical response or assume standard V2 structure.
            # Assuming:
            # { "id": "...", "payment_options": { "bank_slip": { "barcode": "...", "digitable": "...", "url": "..." } } }
            
            boleto_id = data.get('id')
            bank_slip = data.get('payment_options', {}).get('bank_slip', {})
            
            boleto = BoletoCora.objects.create(
                nfse=nfse_obj,
                cliente=nfse_obj.cliente,
                cora_id=boleto_id,
                valor=nfse_obj.servico.sale_price,
                status='Aberto',
                linha_digitavel=bank_slip.get('digitable'),
                codigo_barras=bank_slip.get('barcode'),
                url_pdf=bank_slip.get('url'),
                data_vencimento=due_date
            )

            return boleto

    def simular_pagamento(self, boleto_obj):
        """
        Simula o pagamento de um boleto no ambiente de Sandbox da Cora.
        """
        config = CoraConfig.objects.first()
        if not config or config.ambiente != 2: # 2 = Homologação
            raise Exception("Simulação permitida apenas em ambiente de Homologação.")

        # 1. Get Access Token
        auth = CoraAuth()
        access_token = auth.get_access_token()

        # 2. Prepare Request
        url = f"https://matls-clients.api.stage.cora.com.br/v2/invoices/{boleto_obj.cora_id}/payments"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'Idempotency-Key': str(uuid.uuid4())
        }
        
        payload = {
            "payment_date": timezone.now().strftime('%Y-%m-%d')
        }

        # 3. Send Request
        with mTLS_cert_paths() as cert_files:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                cert=cert_files,
                timeout=30
            )

            if response.status_code != 200:
                raise Exception(f"Erro ao simular pagamento: {response.status_code} - {response.text}")

            # 4. Update Local Status
            boleto_obj.status = 'Pago'
            boleto_obj.save()
            
            return True
