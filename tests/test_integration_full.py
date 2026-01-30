from django.test import TestCase
from core.models import Person
from estoque.models import Product, StockMovement
from operacional.models import ServiceOrder, ServiceOrderItem
from financeiro.models import AccountReceivable
from decimal import Decimal

class ERPIntegrationTest(TestCase):
    def setUp(self):
        # 1. Criação de Dados Base
        # Adapted: type="CUSTOMER" -> is_client=True
        self.cliente = Person.objects.create(name="Cliente Teste", is_client=True, document="12345678900")
        self.produto = Product.objects.create(name="Cabo UTP", current_stock=100, sale_price=10.00, cost_price=5.00, sku="CABO123")

    def test_fluxo_completo_os(self):
        # 2. Criação da OS
        # Adapted: status="OPEN" -> status="PENDING"
        os = ServiceOrder.objects.create(client=self.cliente, status="PENDING", description="Teste Integração")
        
        # 3. Adição de Itens (Agora usando FK correta)
        item = ServiceOrderItem.objects.create(
            service_order=os, 
            product=self.produto, 
            quantity=10, 
            unit_price=10.00
        )
        
        # Update OS value to match items (optional, but good for consistency)
        os.value = Decimal("100.00")
        os.save()
        
        # 4. Ação: Finalizar OS
        os.status = "COMPLETED"
        os.save() # Isso deve disparar os Signals/Logica

        # === VERIFICAÇÕES (ASSERTIONS) ===
        
        # A. Estoque Baixou?
        self.produto.refresh_from_db()
        print(f"Estoque Final: {self.produto.current_stock}")
        self.assertEqual(self.produto.current_stock, 90, "ERRO: Estoque não baixou corretamente!")
        
        # B. Movimentação Criada?
        movimentacao = StockMovement.objects.last()
        self.assertIsNotNone(movimentacao, "ERRO: Não criou registro de movimentação!")
        self.assertEqual(movimentacao.movement_type, "OUT", "ERRO: Tipo de movimento errado")

        # C. Financeiro Gerado?
        conta = AccountReceivable.objects.filter(client=self.cliente).last()
        self.assertIsNotNone(conta, "ERRO: Não gerou o Contas a Receber!")
        self.assertEqual(conta.amount, Decimal("100.00"), "ERRO: Valor do financeiro incorreto!")
