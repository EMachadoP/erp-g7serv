import json
import uuid
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from ai_core.models import AtendimentoAI

class ERPIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword',
            email='test@example.com'
        )
        self.auth_urls = [
            reverse('financeiro:account_payable_list'),
            reverse('core:dashboard'),
        ]

    def test_authenticated_access(self):
        """Test if authenticated user can access main module URLs (200 OK)"""
        self.client.force_login(self.user)
        for url in self.auth_urls:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code, 200, 
                f"Failed to access {url} as authenticated user"
            )

    def test_unauthenticated_redirection(self):
        """Test if unauthenticated user is redirected to login (302 Redirect)"""
        for url in self.auth_urls:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code, 302, 
                f"URL {url} did not redirect unauthenticated user"
            )
            self.assertIn('/accounts/login/', response.url)

    def test_ai_triage_endpoint(self):
        """Test the AI triage POST endpoint with JSON payload"""
        url = reverse('processar_ia')
        payload = {
            "nome": "João Teste",
            "mensagem": "Gostaria de um orçamento para manutenção"
        }
        
        response = self.client.post(
            url, 
            data=json.dumps(payload), 
            content_type='application/json'
        )
        
        # Verify status and format
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'sucesso')
        self.assertEqual(data['categoria'], 'orcamento')
        self.assertTrue('protocolo' in data)
        self.assertEqual(len(data['protocolo']), 8)
        
        atendimento = AtendimentoAI.objects.get(protocolo=data['protocolo'])
        self.assertEqual(atendimento.cliente_nome, "João Teste")
        self.assertEqual(atendimento.categoria_detectada, "orcamento")

    def test_ai_triage_invalid_content_type(self):
        """Test that the AI endpoint rejects non-JSON content types (415)"""
        url = reverse('processar_ia')
        response = self.client.post(url, data="not a json", content_type='text/plain')
        self.assertEqual(response.status_code, 415)
