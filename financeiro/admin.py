from django.contrib import admin
from .models import AccountPayable, AccountReceivable, FinancialCategory, BankReconciliation, CostCenter

@admin.register(FinancialCategory)
class FinancialCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'type')
    list_filter = ('type',)
    search_fields = ('name',)

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
@admin.register(CostCenter)
class CostCenterAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('name', 'code')
