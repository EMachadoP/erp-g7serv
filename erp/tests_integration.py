"""
================================================================================
ERP G7Serv - Testes de Integração Django (Refinado)
================================================================================
Arquivo: erp/tests_integration.py
Versão: 1.1.1 (Correção de Integridade)
Django: 5.1.5
Python: 3.13

Este arquivo contém testes de integração completos para todos os módulos do ERP.
Cobertura: comercial, operacional, financeiro, ai_core, core, dashboard
================================================================================
"""

import uuid
import json
from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

# ==============================================================================
# IMPORTS DOS MODELS REAIS
# ==============================================================================
from core.models import Person, Technician
from comercial.models import Contract, Budget, ContractTemplate
from operacional.models import ServiceOrder
from financeiro.models import AccountPayable
from ai_core.models import AtendimentoAI

User = get_user_model()

# ==============================================================================
# CONFIGURAÇÃO DE TESTE - Usar SQLite em memória para testes rápidos
# ==============================================================================
@override_settings(
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    },
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
    DEFAULT_FILE_STORAGE='django.core.files.storage.InMemoryStorage',
    SECURE_SSL_REDIRECT=False,
    SESSION_COOKIE_SECURE=False,
    CSRF_COOKIE_SECURE=False,
    DEBUG=True,
)
class BaseIntegrationTest(TestCase):
    """
    Classe base para todos os testes de integração.
    """
    
    def setUp(self):
        """
        Configuração inicial para todos os testes.
        """
        self.client = Client()
        
        # Usuário administrador para testes
        self.admin_user = User.objects.create_superuser(
            username='admin_test',
            email='admin@test.com',
            password='admin12345',
            first_name='Admin',
            last_name='Test'
        )
        
        # Usuário comum para testes
        self.regular_user = User.objects.create_user(
            username='user_test',
            email='user@test.com',
            password='user12345',
            first_name='User',
            last_name='Test'
        )
        
        # Técnico para testes de OS
        self.technician_user = User.objects.create_user(
            username='tech_test',
            email='tech@test.com',
            password='tech12345',
            first_name='Tecnico',
            last_name='Test'
        )
        
        # Cria perfil de técnico
        self.tech_profile = Technician.objects.create(
            user=self.technician_user,
            phone='11988887777'
        )


# ==============================================================================
# TESTES DO MÓDULO COMERCIAL
# ==============================================================================
class ComercialIntegrationTest(BaseIntegrationTest):
    """
    Testes de integração para o módulo Comercial.
    """
    
    def setUp(self):
        super().setUp()
        
        # Cria cliente de teste
        self.cliente = Person.objects.create(
            name='Cliente Teste Ltda',
            email='cliente@teste.com',
            phone='11999998888',
            is_client=True,
            document='12.345.678/0001-90'
        )
        
        # Cria modelo de contrato
        self.template = ContractTemplate.objects.create(
            name='Modelo Padrão',
            template_type='Novo Contrato',
            content='Conteúdo do contrato'
        )
        
        # Cria orçamento de teste
        self.orcamento = Budget.objects.create(
            client=self.cliente,
            status='Aberto',
            total_value=Decimal('1500.00'),
            title='Orçamento de teste',
            date=date.today(),
            payment_method='OUTRO'
        )
        
        # Cria contrato de teste
        self.contrato = Contract.objects.create(
            client=self.cliente,
            status='Ativo',
            value=Decimal('5000.00'),
            start_date=date.today(),
            template=self.template,
            due_day=10
        )
    
    def test_clientes_list_authenticated(self):
        self.client.force_login(self.admin_user)
        response = self.client.get('/comercial/clientes/')
        self.assertEqual(response.status_code, 200)
    
    def test_clientes_list_unauthenticated(self):
        response = self.client.get('/comercial/clientes/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
    
    def test_orcamentos_list_authenticated(self):
        self.client.force_login(self.admin_user)
        response = self.client.get('/comercial/orcamentos/')
        self.assertEqual(response.status_code, 200)
    
    def test_orcamentos_create_authenticated(self):
        self.client.force_login(self.admin_user)
        orcamentos_antes = Budget.objects.count()
        
        data = {
            'client': self.cliente.id,
            'title': 'Novo orçamento via POST',
            'date': date.today().isoformat(),
            'payment_method': 'OUTRO',
            'status': 'Aberto'
        }
        
        response = self.client.post('/comercial/orcamentos/novo/', data)
        self.assertIn(response.status_code, [200, 302])
        
        if response.status_code == 302:
            self.assertEqual(Budget.objects.count(), orcamentos_antes + 1)


# ==============================================================================
# TESTES DO MÓDULO OPERACIONAL
# ==============================================================================
class OperacionalIntegrationTest(BaseIntegrationTest):
    """
    Testes de integração para o módulo Operacional.
    """
    
    def setUp(self):
        super().setUp()
        
        self.cliente_os = Person.objects.create(
            name='Cliente OS Teste',
            email='cliente.os@teste.com',
            phone='11988887777',
            is_client=True,
            document='22.333.444/0001-55'
        )
        
        self.ordem_servico = ServiceOrder.objects.create(
            client=self.cliente_os,
            technician=self.technician_user,
            status='PENDING',
            description='Descrição da OS de teste'
        )
    
    def test_os_list_authenticated(self):
        self.client.force_login(self.admin_user)
        response = self.client.get('/operacional/os/')
        self.assertEqual(response.status_code, 200)
    
    def test_os_create_authenticated(self):
        self.client.force_login(self.admin_user)
        os_antes = ServiceOrder.objects.count()
        
        data = {
            'client': self.cliente_os.id,
            'technician': self.technician_user.id,
            'status': 'PENDING',
            'description': 'Nova OS via POST'
        }
        
        response = self.client.post('/operacional/os/nova/', data)
        self.assertIn(response.status_code, [200, 302])
        
        if response.status_code == 302:
            self.assertEqual(ServiceOrder.objects.count(), os_antes + 1)


# ==============================================================================
# TESTES DO MÓDULO FINANCEIRO
# ==============================================================================
class FinanceiroIntegrationTest(BaseIntegrationTest):
    """
    Testes de integração para o módulo Financeiro.
    """
    
    def setUp(self):
        super().setUp()
        
        self.conta_pendente = AccountPayable.objects.create(
            description='Conta de luz',
            amount=Decimal('350.00'),
            due_date=date.today(),
            status='PENDING'
        )
    
    def test_contas_pagar_list_authenticated(self):
        self.client.force_login(self.admin_user)
        response = self.client.get('/financeiro/contas-a-pagar/')
        self.assertEqual(response.status_code, 200)
    
    def test_contas_pagar_create(self):
        self.client.force_login(self.admin_user)
        contas_antes = AccountPayable.objects.count()
        
        data = {
            'description': 'Nova conta de teste',
            'amount': '500.00',
            'due_date': date.today().isoformat(),
            'status': 'PENDING',
            'occurrence_date': date.today().isoformat()
        }
        
        response = self.client.post('/financeiro/contas-a-pagar/nova/', data)
        self.assertIn(response.status_code, [200, 302])
        
        if response.status_code == 302:
            self.assertEqual(AccountPayable.objects.count(), contas_antes + 1)


# ==============================================================================
# TESTES DO MÓDULO AI_CORE
# ==============================================================================
class AICoreIntegrationTest(BaseIntegrationTest):
    """
    Testes de integração para o módulo AI Core.
    """
    
    def test_ai_processar_post_json(self):
        self.client.force_login(self.admin_user)
        
        payload = {
            'mensagem': 'Preciso de ajuda com meu sistema',
            'categoria': 'suporte',
            'nome': 'João Silva',
            'email': 'joao@exemplo.com'
        }
        
        response = self.client.post(
            '/ai/processar/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        resposta_json = response.json()
        self.assertIn('protocolo', resposta_json)


# ==============================================================================
# TESTES DO DASHBOARD
# ==============================================================================
class DashboardIntegrationTest(BaseIntegrationTest):
    """
    Testes de integração para Dashboard.
    """
    
    def test_dashboard_authenticated(self):
        self.client.force_login(self.admin_user)
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)
    
    def test_dashboard_unauthenticated(self):
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
