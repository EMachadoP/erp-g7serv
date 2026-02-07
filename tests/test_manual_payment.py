from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from core.models import Person
from financeiro.models import AccountPayable, CategoriaFinanceira, CashAccount, FinancialTransaction
from datetime import date
from decimal import Decimal

class ManualPaymentTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.login(username='testuser', password='password')
        
        self.supplier = Person.objects.create(name='Test Supplier', is_supplier=True)
        self.category = CategoriaFinanceira.objects.create(nome='Test Category', tipo='saida')
        self.account = CashAccount.objects.create(name='Test Account', initial_balance=1000, current_balance=1000)
        
        self.payable = AccountPayable.objects.create(
            description='Test Payable',
            amount=Decimal('100.00'),
            due_date=date.today(),
            supplier=self.supplier,
            category=self.category,
            status='PENDING'
        )

    def test_manual_payment(self):
        url = reverse('financeiro:realizar_baixa_conta', args=[self.payable.id])
        data = {
            'conta_saida': self.account.id,
            'data_pagamento': date.today().isoformat(),
            'juros': '0',
            'multa': '0',
            'desconto': '0',
            'valor_final': '100.00' 
        }
        
        # Test POST
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Verify DB Updates
        self.payable.refresh_from_db()
        self.assertEqual(self.payable.status, 'PAID')
        self.assertEqual(self.payable.amount, Decimal('100.00'))
        
        # Verify Account Balance Update
        self.account.refresh_from_db()
        self.assertEqual(self.account.current_balance, Decimal('900.00'))
