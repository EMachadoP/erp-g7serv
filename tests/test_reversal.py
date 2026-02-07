from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from core.models import Person
from financeiro.models import AccountPayable, CategoriaFinanceira, CashAccount, FinancialTransaction
from datetime import date
from decimal import Decimal

class PaymentReversalTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.login(username='testuser', password='password')
        
        self.supplier = Person.objects.create(name='Test Supplier', is_supplier=True)
        self.category = CategoriaFinanceira.objects.create(nome='Test Category', tipo='saida')
        self.account = CashAccount.objects.create(name='Test Account', initial_balance=1000, current_balance=1000)
        
        # Create a PAID payable
        self.payable = AccountPayable.objects.create(
            description='Paid Payable',
            amount=Decimal('100.00'),
            due_date=date.today(),
            supplier=self.supplier,
            category=self.category,
            status='PAID',
            payment_date=date.today(),
            account=self.account,
            notes='Pago: R$ 100.00 (Orig: 100.00 + J: 0 + M: 0 - D: 0)'
        )
        # Manually create the transaction that would exist
        FinancialTransaction.objects.create(
            description="Pagamento Paid Payable",
            amount=Decimal('100.00'),
            transaction_type='OUT',
            date=date.today(),
            account=self.account,
            related_payable=self.payable
        )

    def test_reversal(self):
        # Initial check
        self.account.refresh_from_db()
        self.assertEqual(self.account.current_balance, Decimal('900.00')) # 1000 - 100

        url = reverse('financeiro:estornar_conta_pagar', args=[self.payable.id])
        
        # Test POST
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Verify DB Updates
        self.payable.refresh_from_db()
        self.assertEqual(self.payable.status, 'PENDING')
        self.assertIsNone(self.payable.payment_date)
        
        # Verify Transaction Deleted and Balance Restored
        self.assertEqual(FinancialTransaction.objects.filter(related_payable=self.payable).count(), 0)
        self.account.refresh_from_db()
        self.assertEqual(self.account.current_balance, Decimal('1000.00'))
