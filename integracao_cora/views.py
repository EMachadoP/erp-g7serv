from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import CoraConfig
from .forms import CoraConfigForm
from .services.auth import CoraAuth
from django.http import HttpResponse, JsonResponse
from .models import BoletoCora
from faturamento.models import Invoice
from financeiro.models import AccountReceivable, CashAccount, FinancialTransaction
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json
import logging

logger = logging.getLogger(__name__)

class ConfiguracaoCoraView(LoginRequiredMixin, View):
    template_name = 'integracao_cora/configuracao.html'

    def get(self, request):
        config = CoraConfig.objects.first()
        form = CoraConfigForm(instance=config)
        
        status = "Desconectado"
        if config and config.access_token:
            # Simple check: if token exists. Ideally check expiration.
            from django.utils import timezone
            if config.token_expires_at and config.token_expires_at > timezone.now():
                status = "Conectado"
            else:
                status = "Token Expirado"

        return render(request, self.template_name, {
            'form': form,
            'status': status,
            'config': config
        })

    def post(self, request):
        config = CoraConfig.objects.first()
        form = CoraConfigForm(request.POST, request.FILES, instance=config)
        
        if form.is_valid():
            config = form.save()
            
            # Action: Test Connection
            if 'test_connection' in request.POST:
                url_tentada = ""
                try:
                    auth = CoraAuth()
                    url_tentada = auth.URL_PRODUCAO if config.ambiente == 1 else auth.URL_HOMOLOGACAO
                    
                    # Limpa token para forçar reautenticação real
                    config.access_token = None
                    config.token_expires_at = None
                    config.save()
                    
                    token = auth.get_access_token()
                    if token:
                        messages.success(request, f"Conexão realizada com sucesso em {config.get_ambiente_display()}!")
                    else:
                        messages.error(request, "Falha ao obter token.")
                        
                except Exception as e:
                    aviso_ambiente = ""
                    if "invalid_client" in str(e).lower():
                        aviso_ambiente = f" Lembre-se: IDs de Produção só funcionam no ambiente 'Produção'. Atualmente tentando em: {url_tentada}."
                    
                    messages.error(request, f"Erro na conexão: {str(e)}.{aviso_ambiente}")
            # Action: Manual Statement Sync
            elif 'sync_statement' in request.POST:
                try:
                    from .services.statement import CoraStatementService
                    from financeiro.models import CashAccount
                    
                    # Procura a conta Cora
                    account = CashAccount.objects.filter(name__icontains='Cora').first() or \
                              CashAccount.objects.filter(bank_name__icontains='Cora').first()
                    
                    if not account:
                        messages.error(request, "Conta Bancária 'Cora' não encontrada no sistema. Crie-a em Financeiro > Contas.")
                    else:
                        service = CoraStatementService()
                        count, total = service.sync_statement(account)
                        messages.success(request, f"Sincronização realizada! {count} lançamentos processados. Total: R$ {total:.2f}")
                        
                except Exception as e:
                    messages.error(request, f"Erro na sincronização: {str(e)}")
            else:
                messages.success(request, "Configurações salvas com sucesso.")
                
            return redirect('configuracao_cora')
        
        return render(request, self.template_name, {'form': form})

@method_decorator(csrf_exempt, name='dispatch')
class CoraWebhookView(View):
    """
    Recebe notificações de eventos da Cora (Webhooks).
    Principal uso: Baixa automática de boletos pagos.
    """
    def post(self, request):
        try:
            payload = json.loads(request.body)
            logger.info(f"Recebido Webhook Cora: {json.dumps(payload)}")
            
            event_type = payload.get('event')
            data = payload.get('data', {})
            invoice_data = data.get('invoice', {})
            cora_id = invoice_data.get('id')
            status = invoice_data.get('status') # Ex: 'PAID'
            
            # 1. Procurar boleto correspondente
            if cora_id:
                boleto = BoletoCora.objects.filter(cora_id=cora_id).first()
                
                # Evento de pagamento
                if event_type == 'invoice.paid' or status == 'PAID':
                    if boleto:
                        # Atualiza status do boleto
                        boleto.status = 'Pago'
                        boleto.save()
                        
                        # Atualiza status da Fatura se existir
                        if boleto.fatura:
                            boleto.fatura.status = 'PG'
                            boleto.fatura.save()
                        
                        # Atualiza status do Contas a Receber
                        receivable = AccountReceivable.objects.filter(cora_id=cora_id).first()
                        if not receivable and boleto.fatura:
                            receivable = AccountReceivable.objects.filter(invoice=boleto.fatura).first()
                            
                        if receivable and receivable.status != 'RECEIVED':
                            receivable.status = 'RECEIVED'
                            receivable.receipt_date = timezone.now().date()
                            receivable.payment_method = 'PIX/Boleto Cora'
                            receivable.save()
                            
                            # Opcional: Criar movimentação financeira real no caixa padrão
                            account = CashAccount.objects.first() # Pega a primeira conta se não houver selecionada
                            if account:
                                FinancialTransaction.objects.create(
                                    description=f"Recebimento Cora: {receivable.description}",
                                    amount=receivable.amount,
                                    transaction_type='IN',
                                    date=timezone.now().date(),
                                    account=account,
                                    category=receivable.category,
                                    related_receivable=receivable
                                )
                                
                    return HttpResponse("Webhook processed", status=200)

            return HttpResponse("Event ignored", status=200)
            
        except Exception as e:
            logger.error(f"Erro ao processar Webhook Cora: {str(e)}")
            return HttpResponse(f"Error: {str(e)}", status=400)

