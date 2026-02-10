from django.contrib import admin
from django.db import models
from .models import Product, StockMovement, ProductFamily, Brand, Category, StockLocation

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
    list_display = ('sku', 'internal_code', 'name', 'family', 'brand', 'category', 'sale_price', 'current_stock', 'active')
    search_fields = ('sku', 'internal_code', 'name')
    list_filter = ('active', 'family', 'brand', 'category', LowStockFilter)

@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('date', 'movement_type', 'product', 'quantity', 'reason')
    list_filter = ('movement_type', 'date', 'product')
    date_hierarchy = 'date'

@admin.register(ProductFamily)
class ProductFamilyAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(StockLocation)
class StockLocationAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
