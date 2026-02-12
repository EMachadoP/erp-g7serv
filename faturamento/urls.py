from django.urls import path
from . import views

app_name = 'faturamento'
urlpatterns = [
    path('faturas/', views.invoice_list, name='list'),
    path('faturas/nova/', views.invoice_create, name='create'),
    path('faturas/avulsa/nova/', views.invoice_standalone_create, name='standalone_create'),
    path('faturas/<int:pk>/', views.invoice_detail, name='detail'),
    path('faturas/<int:pk>/editar/', views.invoice_update, name='update'),
    path('faturas/<int:pk>/cancelar/', views.invoice_cancel, name='cancel_invoice'),
    path('gerar-os/<int:os_id>/', views.create_invoice_from_os, name='create_from_os'),
    path('gerar-contrato/<int:contract_id>/', views.create_invoice_from_contract, name='create_from_contract'),
    path('faturamento-contratos/', views.contract_billing_view, name='contract_billing'),
    path('faturamento-contratos/buscar/', views.search_contracts, name='search_contracts'),
    path('faturamento-contratos/processar/', views.process_contract_billing, name='process_contract_billing'),
    path('faturamento-contratos/resumo/', views.contract_billing_summary, name='contract_billing_summary'),
    path('faturamento-lote/<int:pk>/', views.billing_batch_detail, name='billing_batch_detail'),
    
    # Ações em Massa para Faturas
    path('faturas/gerar-boletos-lote/', views.invoice_bulk_generate_boletos, name='invoice_bulk_generate_boletos'),
    path('faturas/enviar-emails-lote/', views.invoice_bulk_send_emails, name='invoice_bulk_send_emails'),
    path('faturas/gerar-nfse-lote/', views.invoice_bulk_generate_nfse, name='invoice_bulk_generate_nfse'),
    path('faturas/<int:pk>/nfse/xml/', views.invoice_nfse_xml, name='nfse_xml'),
    path('faturas/<int:pk>/nfse/view/', views.invoice_nfse_view, name='nfse_view'),
    
    # NFe Input (Compras)
    path('notas-entrada/', views.nota_entrada_list, name='nota_entrada_list'),
    path('notas-entrada/nova/', views.nota_entrada_create, name='nota_entrada_create'),
    path('notas-entrada/<int:pk>/', views.nota_entrada_detail, name='nota_entrada_detail'),
    path('notas-entrada/<int:pk>/revisar/', views.nota_entrada_review, name='nota_entrada_review'),
    path('notas-entrada/<int:pk>/lancar/', views.nota_entrada_launch, name='nota_entrada_launch'),
    path('notas-entrada/<int:pk>/estornar/', views.nota_entrada_revert, name='nota_entrada_revert'),
    path('notas-entrada/<int:pk>/excluir/', views.nota_entrada_delete, name='nota_entrada_delete'),
]
