from django.urls import path
from . import views

app_name = 'comercial'
urlpatterns = [
    path('contrato/<uuid:token>/', views.ContractSigningView.as_view(), name='contract_signing'),
    
    # Clients
    path('clientes/', views.client_list, name='client_list'),
    path('clientes/novo/', views.client_create, name='client_create'),
    path('clientes/<int:pk>/', views.client_detail, name='client_detail'),
    path('clientes/<int:pk>/editar/', views.client_update, name='client_update'),
    path('clientes/<int:pk>/excluir/', views.client_delete, name='client_delete'),
    
    # Contracts
    path('contratos/', views.contract_list, name='contract_list'),
    path('contratos/novo/', views.contract_create, name='contract_create'),
    path('contratos/faturar/', views.run_billing, name='run_billing'),
    path('contratos/<int:pk>/', views.contract_detail, name='contract_detail'),
    path('contratos/<int:pk>/editar/', views.contract_update, name='contract_update'),
    path('contratos/<int:pk>/excluir/', views.contract_delete, name='contract_delete'),
    path('contratos/<int:pk>/pdf/', views.contract_pdf, name='contract_pdf'),
    path('contratos/<int:pk>/email/', views.contract_send_email, name='contract_send_email'),
    
    # Contract Templates
    path('modelos-contrato/', views.contract_template_list, name='contract_template_list'),
    path('modelos-contrato/novo/', views.contract_template_create, name='contract_template_create'),
    path('modelos-contrato/<int:pk>/editar/', views.contract_template_update, name='contract_template_update'),
    path('modelos-contrato/<int:pk>/excluir/', views.contract_template_delete, name='contract_template_delete'),
    path('api/modelo-contrato/<int:pk>/', views.get_contract_template_details, name='get_contract_template_details'),
    path('api/cliente/<int:pk>/', views.get_client_details, name='get_client_details'),
    
    # Budgets
    path('orcamentos/', views.budget_list, name='budget_list'),
    path('orcamentos/novo/', views.budget_create, name='budget_create'),
    path('orcamentos/<int:pk>/', views.budget_detail, name='budget_detail'),
    path('orcamentos/<int:pk>/editar/', views.budget_update, name='budget_update'),
    path('orcamentos/<int:pk>/ganhar/', views.budget_win, name='budget_win'),
    path('orcamentos/<int:pk>/recusar/', views.budget_refuse, name='budget_refuse'),
    path('orcamentos/<int:pk>/excluir/', views.budget_delete, name='budget_delete'),
    path('orcamentos/<int:pk>/pdf/', views.budget_pdf, name='budget_pdf'),
    path('orcamentos/<int:pk>/email/', views.budget_send_email, name='budget_send_email'),
    path('acoes-vendas/', views.sales_actions, name='sales_actions'),
    path('orcamentos/<int:pk>/toggle-followup/', views.toggle_followup_strategy, name='toggle_followup_strategy'),
    
    # Services
    path('servicos/', views.service_list, name='service_list'),
    path('servicos/novo/', views.service_create, name='service_create'),
    path('servicos/<int:pk>/editar/', views.service_update, name='service_update'),
    
    # Billing Groups
    path('grupos-faturamento/', views.billing_group_list, name='billing_group_list'),
    path('grupos-faturamento/novo/', views.billing_group_create, name='billing_group_create'),
    path('grupos-faturamento/<int:pk>/editar/', views.billing_group_update, name='billing_group_update'),
    path('grupos-faturamento/<int:pk>/excluir/', views.billing_group_delete, name='billing_group_delete'),
    
    # Contract Readjustments
    path('reajustes/', views.contract_readjustment_list, name='contract_readjustment_list'),
    path('reajustes/novo/', views.contract_readjustment_create, name='contract_readjustment_create'),
    path('reajustes/<int:pk>/desfazer/', views.contract_readjustment_undo, name='contract_readjustment_undo'),
]
