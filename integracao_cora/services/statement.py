import requests
import uuid
from django.utils import timezone
from django.db import transaction
from financeiro.models import FinancialTransaction, AccountReceivable, CashAccount
from integracao_cora.models import CoraConfig
from integracao_cora.services.auth import CoraAuth
from integracao_cora.services.base import mTLS_cert_paths
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

class CoraStatementService:
    URL_PRODUCAO = "https://matls-clients.api.cora.com.br/bank-statement/statement"
    URL_HOMOLOGACAO = "https://matls-clients.api.stage.cora.com.br/bank-statement/statement"

    def sync_statement(self, account, start_date=None, end_date=None):
        """
        Sincroniza o extrato da Cora com o ERP.
        """
        # 1. Autenticação
        auth = CoraAuth()
        access_token = auth.get_access_token()
        
        config = CoraConfig.objects.first()
        url = self.URL_PRODUCAO if config.ambiente == 1 else self.URL_HOMOLOGACAO
        
        # Datas padrão (últimos 7 dias se não informado)
        if not start_date:
            start_date = (timezone.now() - timezone.timedelta(days=7)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = timezone.now().strftime('%Y-%m-%d')
            
        params = {
            'start': start_date,
            'end': end_date
        }
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # 2. Chamada mTLS
        with mTLS_cert_paths() as certs:
            response = requests.get(url, params=params, headers=headers, cert=certs, timeout=30)
            
        if response.status_code != 200:
            raise Exception(f"Erro na API da Cora (Extrato): {response.status_code} - {response.text}")
            
        data = response.json()
        transactions_data = data.get('items', [])
        
        new_count = 0
        total_amount = 0
        
        # 3. Processamento dos Lançamentos
        for item in transactions_data:
            cora_id = item.get('id')
            amount = Decimal(str(item.get('amount', 0))) / Decimal('100.00')  # Cora envia em centavos
            entry_type = item.get('type') # 'CREDIT' or 'DEBIT'
            description = item.get('description', 'Transação Cora')
            transaction_date = item.get('created_at', '').split('T')[0]
            
            # Extract metadata if available
            details = item.get('details', {})
            invoice_id = details.get('invoice_id')
            
            # Evitar duplicidade usando o cora_id
            if FinancialTransaction.objects.filter(external_id=cora_id).exists():
                continue
                
            with transaction.atomic():
                # Determinar tipo
                t_type = 'IN' if entry_type == 'CREDIT' else 'OUT'
                
                # Criar Transação Financeira
                tx = FinancialTransaction.objects.create(
                    description=description,
                    amount=abs(amount),
                    transaction_type=t_type,
                    date=transaction_date,
                    account=account,
                    external_id=cora_id
                )
                
                # 4. Conciliação Automática (Se for crédito)
                if t_type == 'IN':
                    # Tenta encontrar um Contas a Receber correspondente
                    # Geralmente via transaction_id ou referência no description
                    # No caso de boletos Cora, o transaction pode ter o invoice_id
                    if invoice_id:
                        receivable = AccountReceivable.objects.filter(cora_id=invoice_id, status='PENDING').first()
                    
                    if not receivable:
                        # Fallback: Search for a BoletoCora with the invoice_id from details
                        from integracao_cora.models import BoletoCora
                        target_id = invoice_id or cora_id # Usually invoice_id in details
                        boleto = BoletoCora.objects.filter(cora_id=target_id).first()
                        if boleto:
                            if boleto.fatura:
                                receivable = AccountReceivable.objects.filter(invoice=boleto.fatura, status='PENDING').first()
                            elif boleto.nfse:
                                receivable = AccountReceivable.objects.filter(description__icontains=f"#{boleto.nfse.id}", status='PENDING').first()
                                if not receivable and boleto.nfse.fatura:
                                    receivable = AccountReceivable.objects.filter(invoice=boleto.nfse.fatura, status='PENDING').first()
                    
                    if receivable:
                        receivable.status = 'RECEIVED'
                        receivable.receipt_date = transaction_date
                        receivable.payment_method = 'Boleto/PIX Cora (Sinc)'
                        receivable.save()
                        
                        tx.related_receivable = receivable
                        tx.save()
                
                new_count += 1
                total_amount += abs(amount)
                
        return new_count, total_amount
