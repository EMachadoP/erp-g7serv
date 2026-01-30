from django.contrib import admin
from django.utils.html import mark_safe
from .models import ServiceOrder, OSAnexo, ServiceOrderItem

class OSAnexoInline(admin.TabularInline):
    model = OSAnexo
    extra = 0
    readonly_fields = ('preview',)
    
    def preview(self, obj):
        if obj.file:
            return mark_safe(f'<img src="{obj.file.url}" width="100" />')
        return "-"

class ServiceOrderItemInline(admin.TabularInline):
    model = ServiceOrderItem
    extra = 1

@admin.register(ServiceOrder)
class ServiceOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'status', 'start_date', 'checkin_map_link')
    list_filter = ('status', 'start_date')
    search_fields = ('client__name', 'description', 'solution')
    inlines = [ServiceOrderItemInline, OSAnexoInline]
    readonly_fields = ('checkin_lat', 'checkin_long', 'checkin_time', 'checkout_time', 'signature_preview')
    
    def signature_preview(self, obj):
        if obj.signature_image:
            return mark_safe(f'<img src="{obj.signature_image.url}" width="200" style="background:white; border:1px solid #ccc;" />')
        return "Sem assinatura"
    signature_preview.short_description = "Assinatura do Cliente"

    def checkin_map_link(self, obj):
        if obj.checkin_lat and obj.checkin_long:
            url = f"https://maps.google.com/?q={obj.checkin_lat},{obj.checkin_long}"
            return mark_safe(f'<a href="{url}" target="_blank">Ver no Mapa</a>')
        return "-"
    checkin_map_link.short_description = "Local do Check-in"
