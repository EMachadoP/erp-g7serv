from django.contrib import admin
from .models import Person, Service, CompanySettings

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'fantasy_name', 'document', 'is_client', 'is_supplier', 'is_collaborator', 'active')
    search_fields = ('name', 'fantasy_name', 'document')
    list_filter = ('active', 'is_client', 'is_supplier', 'is_collaborator', 'state')
    fieldsets = (
        ('Identificação', {
            'fields': ('name', 'fantasy_name', 'person_type', 'document', 'state_registration')
        }),
        ('Tipo', {
            'fields': ('is_client', 'is_supplier', 'is_collaborator')
        }),
        ('Contato', {
            'fields': ('email', 'phone')
        }),
        ('Endereço', {
            'fields': ('zip_code', 'address', 'number', 'complement', 'neighborhood', 'codigo_municipio_ibge', 'city', 'state')
        }),
        ('Status', {
            'fields': ('active',)
        }),
    )

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_cost', 'sale_price', 'active')
    search_fields = ('name',)

@admin.register(CompanySettings)
class CompanySettingsAdmin(admin.ModelAdmin):
    list_display = ('name', 'cnpj')
