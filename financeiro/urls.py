from django.urls import path
from . import views
from faturamento import views as views_faturamento

app_name = 'financeiro'
urlpatterns = [
    path('', views.financial_dashboard, name='dashboard'),
    
    # Contas a Pagar
    path('contas-a-pagar/', views.account_payable_list, name='account_payable_list'),
    path('contas-a-pagar/nova/', views.account_payable_create, name='account_payable_create'),
    path('contas-a-pagar/<int:pk>/', views.account_payable_detail, name='account_payable_detail'),
    path('contas-a-pagar/<int:pk>/pagar/', views.baixa_conta_pagar, name='account_payable_pay'),
    path('contas-a-pagar/<int:pk>/cancelar/', views.cancelar_conta_pagar, name='account_payable_cancel'),
    path('realizar_baixa_conta/<int:pk>/', views.realizar_baixa_conta, name='realizar_baixa_conta'),
    path('estornar_conta_pagar/<int:pk>/', views.estornar_conta_pagar, name='estornar_conta_pagar'),

    # Contas a Receber
    path('contas-a-receber/', views.account_receivable_list, name='account_receivable_list'),
    path('contas-a-receber/nova/', views.account_receivable_create, name='account_receivable_create'),
    path('contas-a-receber/sincronizar/', views.sync_receables_view, name='sync_receivables'),
    path('contas-a-receber/diagnostico/', views.receivables_diagnostics, name='receivables_diagnostics'),
    path('contas-a-receber/<int:pk>/', views.account_receivable_detail, name='account_receivable_detail'),
    path('contas-a-receber/<int:pk>/editar/', views.account_receivable_update, name='account_receivable_update'),
    path('contas-a-receber/<int:pk>/receber/', views.account_receivable_receive, name='account_receivable_receive'),
    path('contas-a-receber/<int:pk>/cancelar/', views.account_receivable_cancel, name='account_receivable_cancel'),
    path('contas-a-receber/<int:pk>/emitir-boleto/', views.emitir_boleto_cora, name='emitir_boleto_cora'),
    
    # Receipts
    path('recibos/', views.receipt_list, name='receipt_list'),
    path('recibos/novo/', views.receipt_create, name='receipt_create'),
    path('recibos/<int:pk>/imprimir/', views.receipt_print, name='receipt_print'),
    
    # Budget Planning
    path('planejamento/', views.budget_plan_list, name='budget_plan_list'),
    path('planejamento/novo/', views.budget_plan_create, name='budget_plan_create'),
    path('planejamento/<int:pk>/', views.budget_plan_detail, name='budget_plan_detail'),
    path('planejamento/item/update/', views.budget_item_update, name='budget_item_update'),
    
    # Batch Billing (Requested in Passo 3)
    path('processar-lote/', views_faturamento.process_contract_billing, name='process_batch_billing'),
    
    # Batch Actions
    path('contas-a-receber/gerar-boletos-lote/', views.bulk_generate_boletos, name='bulk_generate_boletos'),
    path('contas-a-receber/enviar-emails-lote/', views.bulk_send_emails, name='bulk_send_emails'),
    
    # Diagnóstico Cora mTLS
    path('diagnostico/cora/', views.testar_conexao_cora, name='diagnostico_cora'),
    path('diagnostico/email/', views.testar_conexao_email, name='diagnostico_email'),
]
