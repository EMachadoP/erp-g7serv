from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import CoraConfig
from .forms import CoraConfigForm
from .services.auth import CoraAuth

class ConfiguracaoCoraView(LoginRequiredMixin, View):
    template_name = 'integracao_cora/configuracao.html'

    def get(self, request):
        config = CoraConfig.objects.first()
        form = CoraConfigForm(instance=config)
        
        status = "Desconectado"
        if config and config.access_token:
            # Simple check: if token exists. Ideally check expiration.
            from django.utils import timezone
            if config.token_expires_at and config.token_expires_at > timezone.now():
                status = "Conectado"
            else:
                status = "Token Expirado"

        return render(request, self.template_name, {
            'form': form,
            'status': status,
            'config': config
        })

    def post(self, request):
        config = CoraConfig.objects.first()
        form = CoraConfigForm(request.POST, request.FILES, instance=config)
        
        if form.is_valid():
            config = form.save()
            
            # Action: Test Connection
            if 'test_connection' in request.POST:
                try:
                    auth = CoraAuth()
                    # Force new token to verify credentials
                    # We can't easily force new token with current logic unless we clear it first
                    # or just call get_access_token() which validates existing or fetches new.
                    # To really test credentials, let's clear the token first temporarily?
                    # Or just trust get_access_token logic.
                    
                    # Let's try to fetch a token. If credentials are wrong, it will fail.
                    # But if a valid token exists in DB, it returns it without hitting API.
                    # So to test NEW credentials, we should clear the token.
                    
                    config.access_token = None
                    config.token_expires_at = None
                    config.save()
                    
                    token = auth.get_access_token()
                    if token:
                        messages.success(request, "Conexão realizada com sucesso! Token obtido.")
                    else:
                        messages.error(request, "Falha ao obter token.")
                        
                except Exception as e:
                    messages.error(request, f"Erro na conexão: {str(e)}")
            else:
                messages.success(request, "Configurações salvas com sucesso.")
                
            return redirect('configuracao_cora')
        
        return render(request, self.template_name, {'form': form})
