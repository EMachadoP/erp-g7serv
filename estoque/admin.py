from django.contrib import admin
from .models import Product, StockMovement

class LowStockFilter(admin.SimpleListFilter):
    title = 'Estoque Baixo'
    parameter_name = 'low_stock'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Abaixo do Mínimo'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(current_stock__lt=models.F('minimum_stock'))
        return queryset

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('sku', 'name', 'sale_price', 'current_stock', 'minimum_stock', 'active')
    search_fields = ('sku', 'name')
    list_filter = ('active', LowStockFilter)

@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('date', 'movement_type', 'product', 'quantity', 'reason')
    list_filter = ('movement_type', 'date', 'product')
    date_hierarchy = 'date'
