from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from core.models import Person
from financeiro.models import AccountPayable, CategoriaFinanceira, CashAccount
from datetime import date
from decimal import Decimal

class AccountPayableDetailQATest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.login(username='testuser', password='password')
        
        self.supplier = Person.objects.create(name='Test Supplier', is_supplier=True)
        self.category = CategoriaFinanceira.objects.create(nome='Test Category', tipo='saida')
        self.account = CashAccount.objects.create(name='Test Account', initial_balance=1000)
        
        self.payable = AccountPayable.objects.create(
            description='Test Payable',
            amount=Decimal('500.00'),
            due_date=date.today(),
            supplier=self.supplier,
            category=self.category,
            status='PENDING'
        )

    def test_detail_view_renders_modal(self):
        url = reverse('financeiro:account_payable_detail', args=[self.payable.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        
        # Check basic content
        self.assertIn('Detalhes da Conta a Pagar', content)
        # Check for amount (handling localization 500,00 or 500.00)
        self.assertTrue('500,00' in content or '500.00' in content)
        
        # Check for Modal Trigger Button
        self.assertIn('data-bs-target="#modalPagamento"', content)
        
        # Check for Modal Content
        self.assertIn('id="modalPagamento"', content)
        self.assertIn('Registrar Pagamento', content)
        
        # Check for Form Fields (from PaymentPayableForm)
        self.assertIn('id_interest', content)
        self.assertIn('id_fine', content)
        self.assertIn('id_discount', content)
        # JS Check
        self.assertIn('document.getElementById', content)
