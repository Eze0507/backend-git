from django.contrib import admin
from .modelsFactProv import FacturaProveedor
from .modelsDetallesFactProv import DetalleFacturaProveedor

@admin.register(FacturaProveedor)
class FacturaProveedorAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'numero', 'proveedor', 'fecha_registro', 'total', 'descuento', 'impuesto'
    )
    search_fields = ('numero', 'proveedor__nombre')
    list_filter = ('proveedor', 'fecha_registro')
    ordering = ('-fecha_registro',)

@admin.register(DetalleFacturaProveedor)
class DetalleFacturaProveedorAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'factura', 'item', 'cantidad', 'precio', 'descuento', 'subtotal', 'total'
    )
    search_fields = ('factura__numero', 'item__nombre')
    list_filter = ('factura', 'item')
    ordering = ('id',)
