
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from core.models import Person
from financeiro.models import AccountPayable, FinancialCategory, CashAccount, FinancialTransaction
from datetime import date
from decimal import Decimal

class PaymentLogicTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.login(username='testuser', password='password')
        
        self.supplier = Person.objects.create(name='Test Supplier', is_supplier=True)
        self.category = FinancialCategory.objects.create(name='Test Category', type='EXPENSE')
        self.account = CashAccount.objects.create(name='Test Account', initial_balance=1000)
        
        self.payable = AccountPayable.objects.create(
            description='Test Payable',
            amount=Decimal('100.00'),
            due_date=date.today(),
            supplier=self.supplier,
            category=self.category,
            status='PENDING'
        )

    def test_payment_updates_status(self):
        url = reverse('financeiro:account_payable_pay', args=[self.payable.id])
        data = {
            'amount': '100.00',
            'payment_date': date.today().isoformat(),
            'account': self.account.id,
            'interest': '0.00',
            'fine': '0.00',
            'discount': '0.00'
        }
        
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Reload object
        self.payable.refresh_from_db()
        self.assertEqual(self.payable.status, 'PAID')
        self.assertEqual(self.payable.amount, Decimal('100.00'))
        self.assertEqual(self.payable.account, self.account)
        
        # Check Transaction
        self.assertTrue(FinancialTransaction.objects.filter(related_payable=self.payable).exists())
