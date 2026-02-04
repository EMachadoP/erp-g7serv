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
                url_tentada = ""
                try:
                    auth = CoraAuth()
                    url_tentada = auth.URL_PRODUCAO if config.ambiente == 1 else auth.URL_HOMOLOGACAO
                    
                    # Limpa token para forçar reautenticação real
                    config.access_token = None
                    config.token_expires_at = None
                    config.save()
                    
                    token = auth.get_access_token()
                    if token:
                        messages.success(request, f"Conexão realizada com sucesso em {config.get_ambiente_display()}!")
                    else:
                        messages.error(request, "Falha ao obter token.")
                        
                except Exception as e:
                    aviso_ambiente = ""
                    if "invalid_client" in str(e).lower():
                        aviso_ambiente = f" Lembre-se: IDs de Produção só funcionam no ambiente 'Produção'. Atualmente tentando em: {url_tentada}."
                    
                    messages.error(request, f"Erro na conexão: {str(e)}.{aviso_ambiente}")
            else:
                messages.success(request, "Configurações salvas com sucesso.")
                
            return redirect('configuracao_cora')
        
        return render(request, self.template_name, {'form': form})
