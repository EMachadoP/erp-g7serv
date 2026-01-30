from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

# Transactional Models to Delete
from operacional.models import ServiceOrder, ServiceOrderItem
from comercial.models import Budget, Contract
from financeiro.models import AccountReceivable, AccountPayable, Transaction
from faturamento.models import Invoice, NotaEntrada
from estoque.models import StockMovement, Product
from integracao_cora.models import BoletoCora
from nfse_nacional.models import NFSe

# Base Models to Keep:
# - core.Person (Clients, Suppliers, Employees)
# - core.Service
# - estoque.Product (but reset stock)
# - integracao_cora.CoraConfig (config)
# - nfse_nacional.Empresa (config)

class Command(BaseCommand):
    help = 'LIMPA todas as tabelas transacionais (OS, Financeiro, Estoque) mantendo cadastros base.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-input',
            action='store_true',
            help='Pula a confirmação (CUIDADO: APAGA DADOS)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("!!! ATENÇÃO: ESTE COMANDO IRÁ APAGAR TODAS AS MOVIMENTAÇÕES DO SISTEMA !!!"))
        self.stdout.write("Serão apagados: OS, Orçamentos, Contratos, Faturas, Contas a Receber/Pagar, Movimento de Estoque, Notas Fiscais.")
        self.stdout.write("Serão MANTIDOS: Clientes, Produtos (estoque zerado), Serviços, Usuários, Configurações.")

        if not options['no_input']:
            confirm = input("\nPara confirmar, digite 'RESETAR' (tudo maiúsculo): ")
            if confirm != 'RESETAR':
                self.stdout.write(self.style.ERROR("Operação cancelada."))
                return

        try:
            with transaction.atomic():
                self.stdout.write("Apagando Integrações (Boletos, NFSe)...")
                BoletoCora.objects.all().delete()
                NFSe.objects.all().delete()

                self.stdout.write("Apagando Faturamento e Notas de Entrada...")
                Invoice.objects.all().delete()
                NotaEntrada.objects.all().delete()

                self.stdout.write("Apagando Financeiro (Receber, Pagar, Transações)...")
                # Order matters if logic exists, but delete() usually handles cascade.
                # Transaction usually depends on AccountReceivable/Payable or vice versa?
                # Deleting Receivables/Payables first.
                AccountReceivable.objects.all().delete()
                AccountPayable.objects.all().delete()
                Transaction.objects.all().delete()

                self.stdout.write("Apagando Operacional/Comercial (OS, Orçamentos, Contratos)...")
                ServiceOrder.objects.all().delete() # Cascades to Items
                Budget.objects.all().delete()
                Contract.objects.all().delete()

                self.stdout.write("Apagando Estoque e Zerando Produtos...")
                StockMovement.objects.all().delete()
                
                # Reset Product Stock
                products = Product.objects.all()
                count = products.update(current_stock=0)
                self.stdout.write(f"Estoque zerado para {count} produtos.")

                self.stdout.write(self.style.SUCCESS("\n[SUCESSO] Todas as tabelas de movimentação foram limpas!"))
                self.stdout.write(self.style.SUCCESS("O sistema está pronto para novos testes/uso."))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro ao limpar dados: {e}"))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
