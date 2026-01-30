
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from financeiro.models import AccountPayable, CashAccount
from core.models import Person

class AccountPayableTemplateTest(TestCase):
    def setUp(self):
        # Create a user and login
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client = Client()
        self.client.login(username='testuser', password='password')
        
        # Setup data is not strictly necessary for TemplateSyntaxError check unless specific context objects break it,
        # but good to have minimal context.
        
    def test_account_payable_list_renders_200(self):
        """
        QA Protocol: Verify that the account payable list renders with status 200.
        This catches TemplateSyntaxErrors and 500s.
        """
        # Using name 'financeiro:account_payable_list' based on history
        try:
            url = reverse('financeiro:account_payable_list')
        except:
             # Fallback if I got the name wrong, hardcode common path
            url = '/financeiro/contas-a-pagar/'
            
        print(f"Testing URL: {url}")
        
        response = self.client.get(url)
        
        if response.status_code != 200:
            print(f"Status Code: {response.status_code}")
            # If it's a template error, it might show in content or stderr
            # print(response.content.decode('utf-8')) 
            
        self.assertEqual(response.status_code, 200, f"Failed to render {url}. Status: {response.status_code}")
