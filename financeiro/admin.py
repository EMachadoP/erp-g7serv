from django.contrib import admin
from .models import (
    AccountPayable, AccountReceivable, CategoriaFinanceira, BankReconciliation, 
    CentroResultado, CashAccount, Receipt, BudgetPlan, BudgetItem, 
    EmpresaFiscal, NotaFiscalServico
)

@admin.register(CategoriaFinanceira)
class CategoriaFinanceiraAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'grupo_dre', 'ordem_exibicao')
    list_filter = ('tipo', 'grupo_dre')
    search_fields = ('nome', 'grupo_dre')

@admin.register(CentroResultado)
class CentroResultadoAdmin(admin.ModelAdmin):
    list_display = ('code', 'nome', 'ativo')
    search_fields = ('nome', 'code')
    list_filter = ('ativo',)

@admin.register(AccountPayable)
class AccountPayableAdmin(admin.ModelAdmin):
    list_display = ('description', 'supplier', 'amount', 'due_date', 'status')
    list_filter = ('status', 'due_date', 'category')
    search_fields = ('description', 'supplier__name')
    actions = ['mark_as_paid']

    def mark_as_paid(self, request, queryset):
        queryset.update(status='PAID')
    mark_as_paid.short_description = "Marcar como paga"

@admin.register(AccountReceivable)
class AccountReceivableAdmin(admin.ModelAdmin):
    list_display = ('description', 'client', 'amount', 'due_date', 'status')
    list_filter = ('status', 'due_date', 'category')
    search_fields = ('description', 'client__name')
    actions = ['mark_as_received']

    def mark_as_received(self, request, queryset):
        queryset.update(status='RECEIVED')
    mark_as_received.short_description = "Marcar como recebida"

@admin.register(BankReconciliation)
class BankReconciliationAdmin(admin.ModelAdmin):
    list_display = ('date', 'description', 'amount', 'transaction_type')
    list_filter = ('transaction_type', 'date')
    search_fields = ('description',)

@admin.register(CashAccount)
class CashAccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'bank_name', 'current_balance')
    search_fields = ('name', 'bank_name')

@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ('id', 'person', 'amount', 'issue_date', 'type')
    list_filter = ('type', 'issue_date')
    search_fields = ('description', 'person__name')

admin.site.register(BudgetPlan)
admin.site.register(BudgetItem)

@admin.register(EmpresaFiscal)
class EmpresaFiscalAdmin(admin.ModelAdmin):
    list_display = ('cnpj', 'inscricao_municipal', 'codigo_municipio_ibge', 'regime_tributario')

@admin.register(NotaFiscalServico)
class NotaFiscalServicoAdmin(admin.ModelAdmin):
    list_display = ('numero_dps', 'cliente', 'valor_total', 'status', 'protocolo')
    list_filter = ('status', 'serie')
    search_fields = ('cliente__name', 'protocolo')
