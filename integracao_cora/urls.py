from django.urls import path
from .views import ConfiguracaoCoraView

urlpatterns = [
    path('financeiro/configuracoes/cora/', ConfiguracaoCoraView.as_view(), name='configuracao_cora'),
]
