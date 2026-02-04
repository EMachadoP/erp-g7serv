from django.urls import path
from .views import ConfiguracaoCoraView, CoraWebhookView

urlpatterns = [
    path('financeiro/configuracoes/cora/', ConfiguracaoCoraView.as_view(), name='configuracao_cora'),
    path('financeiro/webhook/cora/', CoraWebhookView.as_view(), name='cora_webhook'),
]
