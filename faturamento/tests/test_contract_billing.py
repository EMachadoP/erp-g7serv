from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.utils import timezone
from datetime import date
from decimal import Decimal
from core.models import Person
from comercial.models import Contract, BillingGroup, ContractTemplate
from faturamento.models import Invoice
from financeiro.models import AccountReceivable

class ContractBillingTest(TestCase):
    def setUp(self):
        # Create User and Login
        self.user = User.objects.create_user(username='testuser', password='password')
        # Add permissions
        permissions = Permission.objects.filter(codename__in=[
            'view_contract', 'add_invoice', 'view_invoice', 'add_accountreceivable'
        ])
        self.user.user_permissions.set(permissions)
        self.client = Client()
        self.client.login(username='testuser', password='password')

        # Create Client
        self.person = Person.objects.create(
            name="Cliente Teste",
            is_client=True
        )

        # Create Billing Group
        self.group = BillingGroup.objects.create(name="Grupo Teste", active=True)

        # Create Contract Template
        self.template = ContractTemplate.objects.create(
            name="Modelo Teste",
            template_type="Novo Contrato",
            content="Conteúdo do contrato"
        )

        # Create Contract
        self.contract = Contract.objects.create(
            client=self.person,
            billing_group=self.group,
            template=self.template,
            value=Decimal('1000.00'),
            due_day=10,
            status='Ativo',
            start_date=date(2025, 1, 1)
        )

    def test_search_contracts(self):
        """Test searching for contracts to bill."""
        url = reverse('faturamento:search_contracts')
        response = self.client.get(url, {
            'month': 2,
            'year': 2025,
            'group': self.group.id
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['contracts']), 1)
        self.assertEqual(data['contracts'][0]['id'], self.contract.id)

    def test_process_billing(self):
        """Test processing the billing for a contract."""
        url = reverse('faturamento:process_contract_billing')
        data = {
            'competence_month': 2,
            'competence_year': 2025,
            'selected_contracts': [self.contract.id]
        }
        response = self.client.post(url, data, follow=True)
        self.assertRedirects(response, reverse('faturamento:contract_billing_summary'))

        # Verify Invoice Created
        invoice = Invoice.objects.get(contract=self.contract, competence_month=2, competence_year=2025)
        self.assertEqual(invoice.amount, Decimal('1000.00'))
        self.assertEqual(invoice.status, 'PD')

        # Verify Account Receivable Created
        receivable = AccountReceivable.objects.get(invoice=invoice)
        self.assertEqual(receivable.amount, Decimal('1000.00'))
        self.assertEqual(receivable.client, self.person)

    def test_prevent_double_billing(self):
        """Test that the same contract is not billed twice for the same period."""
        # First billing
        self.test_process_billing()

        # Try to search again
        url = reverse('faturamento:search_contracts')
        response = self.client.get(url, {
            'month': 2,
            'year': 2025,
            'group': self.group.id
        })
        data = response.json()
        self.assertEqual(len(data['contracts']), 0) # Should be empty

        # Try to force post again
        url_process = reverse('faturamento:process_contract_billing')
        data_post = {
            'competence_month': 2,
            'competence_year': 2025,
            'selected_contracts': [self.contract.id]
        }
        self.client.post(url_process, data_post)
        
        # Check that we still have only 1 invoice
        count = Invoice.objects.filter(contract=self.contract, competence_month=2, competence_year=2025).count()
        self.assertEqual(count, 1)
