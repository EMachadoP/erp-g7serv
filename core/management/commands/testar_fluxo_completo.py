import datetime
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.management import call_command
from django.db import transaction

# Models
from core.models import Person
from estoque.models import Product
from comercial.models import Contract, ContractTemplate, BillingGroup
from financeiro.models import AccountReceivable, FinancialCategory
from operacional.models import ServiceOrder, ServiceOrderItem
from integracao_cora.models import CoraConfig
from integracao_cora.services.boleto import CoraBoleto
from nfse_nacional.models import NFSe, Empresa
from core.models import Service

from comercial.management.commands.processar_contratos import Command as ProcessarContratosCommand

class Command(BaseCommand):
    help = 'Executa um diagnóstico completo do fluxo do ERP (Comercial -> Operacional -> Financeiro -> Integrações)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO('Starting System Diagnostic...'))
        
        # Test Data Containers (for cleanup)
        self.test_data = {}

        try:
            with transaction.atomic():
                self.setup_data()
                
                self.test_step_1_commercial_financial()
                self.test_step_2_operational_stock()
                self.test_step_3_integrations()

                self.stdout.write(self.style.SUCCESS('\n[SUCESSO] O sistema está operando 100%.'))
                
                # Rollback changes after test
                raise Exception("ROLLBACK_TEST")

        except Exception as e:
            if str(e) == "ROLLBACK_TEST":
                self.stdout.write(self.style.SUCCESS("Diagnostic completed successfully. (Data rolled back)"))
            else:
                self.stdout.write(self.style.ERROR(f'\n[FALHA] Erro durante o teste: {e}'))
                import traceback
                self.stdout.write(self.style.ERROR(traceback.format_exc()))

    def setup_data(self):
        self.stdout.write('Setting up test environment...')
        
        # 1. Financial Categories
        self.cat_revenue, _ = FinancialCategory.objects.get_or_create(
            name='Receita Teste', 
            defaults={'type': 'REVENUE'}
        )
        
        # 2. Client
        self.client = Person.objects.create(
            name='Cliente Teste Automático',
            person_type='PJ',
            document='00000000000191', # Dummy CNPJ
            is_client=True
        )
        
        # 3. Product
        self.product = Product.objects.create(
            name='Produto Teste Fluxo',
            sku='TEST-001',
            sale_price=Decimal('100.00'),
            cost_price=Decimal('50.00'),
            current_stock=10
        )
        
        # 4. Contract Helpers
        self.template = ContractTemplate.objects.create(name='Template Teste', content='Texto')
        self.group = BillingGroup.objects.create(name='Grupo Teste')

    def test_step_1_commercial_financial(self):
        self.stdout.write('\n>>> Etapa 1: Comercial/Financeiro (Contrato -> Fatura)')
        
        # Create Contract Due Today
        today = timezone.now().date()
        contract = Contract.objects.create(
            client=self.client,
            template=self.template,
            billing_group=self.group,
            value=Decimal('1000.00'),
            due_day=today.day,
            status='Ativo',
            start_date=today,
            modality='Mensal'
        )
        
        # Call Command Routine Directly with Capture
        self.stdout.write(f'Calling processar_contratos logic for Contract #{contract.id}...')
        
        from io import StringIO
        cmd_output = StringIO()
        cmd = ProcessarContratosCommand()
        cmd.stdout = cmd_output 
        
        # Patch to process ONLY our test contract
        with patch('comercial.management.commands.processar_contratos.Contract.objects.filter') as mock_filter:
            mock_filter.return_value = [contract]
            cmd.handle()
        
        full_output = cmd_output.getvalue()
        
        # Assertions
        fatura = AccountReceivable.objects.filter(
            client=self.client,
            amount=Decimal('1000.00'),
            description__contains=f"Contrato #{contract.id}"
        ).first()
        
        if fatura:
            self.stdout.write(self.style.SUCCESS('[OK] Contrato gerou financeiro.'))
        else:
            cats = FinancialCategory.objects.filter(type='REVENUE').values_list('name', flat=True)
            recs = AccountReceivable.objects.filter(client=self.client).values('description', 'amount')
            debug_extra = f"Cats: {list(cats)}. Recs found: {list(recs)}. \nCMD OUTPUT: {full_output}"
            raise Exception(f'Contrato NÃO gerou ContaReceber. Extra: {debug_extra}')

    def test_step_2_operational_stock(self):
        self.stdout.write('\n>>> Etapa 2: Operacional/Estoque (OS -> Baixa)')
        
        # Create OS
        os = ServiceOrder.objects.create(
            client=self.client,
            status='PENDING',
            scheduled_date=timezone.now()
        )
        
        # Add Item (Product, Qty 1)
        ServiceOrderItem.objects.create(
            service_order=os,
            product=self.product,
            unit_price=self.product.sale_price,
            quantity=1
        )
        
        # Finish OS
        os.status = 'COMPLETED'
        os.save()
        
        # Reload Product
        self.product.refresh_from_db()
        
        # Assert Stock
        if self.product.current_stock == 9:
             self.stdout.write(self.style.SUCCESS('[OK] OS baixou estoque (10 -> 9).'))
        else:
            raise Exception(f'Estoque não baixou corretamente. Atual: {self.product.current_stock}')
            
        # Assert Financeiro (Signal)
        # Check for receivable for this OS
        fatura_os = AccountReceivable.objects.filter(
            description__contains=f"Ref. OS #{os.id}"
        ).first()

        if fatura_os:
             self.stdout.write(self.style.SUCCESS('[OK] OS gerou financeiro.'))
        else:
             # Warning only? Or Error? User asked "Assert: Verificar se gerou..."
             # If logic exists, it should be error.
             # I saw the signal in operational/signals.py, so it should exist.
             raise Exception('OS Finalizada NÃO gerou conta a receber.')

    def test_step_3_integrations(self):
        self.stdout.write('\n>>> Etapa 3: Integrações (Simulação Cora)')
        
        # Mocking Cora
        with patch('integracao_cora.services.auth.CoraAuth.get_access_token') as mock_token, \
             patch('requests.post') as mock_post:
            
            mock_token.return_value = "fake_token_123"
            
            # Mock Response for Boleto Generation
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": "cora_boleto_fake_id",
                "payment_options": {
                    "bank_slip": {
                        "barcode": "123456",
                        "digitable": "123456789",
                        "url": "http://cora.fake/boleto.pdf"
                    }
                }
            }
            mock_post.return_value = mock_response
            
            # Setup Config if missing
            if not CoraConfig.objects.exists():
                CoraConfig.objects.create(client_id='x', client_secret='y', ambiente=2)

            # Create Dependencies for NFSe
            empresa, _ = Empresa.objects.get_or_create(
                cnpj='12345678000199', 
                defaults={
                    'razao_social': 'Empresa Teste', 
                    'ambiente': 2,
                    'codigo_mun_ibge': '2611606'
                }
            )
            
            service, _ = Service.objects.get_or_create(
                name='Serviço Teste NFSe',
                defaults={'sale_price': Decimal('50.00'), 'base_cost': Decimal('10.00')}
            )

            # Create Real NFSe
            nfse_real = NFSe.objects.create(
                empresa=empresa,
                cliente=self.client,
                servico=service
            )
            
            # Execute
            cora_service = CoraBoleto()
            boleto = cora_service.gerar_boleto(nfse_real)
            
            if boleto and boleto.cora_id == "cora_boleto_fake_id":
                self.stdout.write(self.style.SUCCESS('[OK] Integração Cora simulada com sucesso.'))
            else:
                raise Exception("Falha ao gerar boleto simulado (Objeto não retornado ou ID incorreto).")
