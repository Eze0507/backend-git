from django.contrib import admin
from .modelsArea import Area
from .modelsItem import Item
from .modelsVehiculos import Vehiculo, Marca, Modelo
from .modelsProveedor import Proveedor

@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ['nombre']
    search_fields = ['nombre']
    ordering = ['nombre']

@admin.register(Modelo)
class ModeloAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'marca']
    list_filter = ['marca']
    search_fields = ['nombre', 'marca__nombre']
    ordering = ['marca__nombre', 'nombre']

@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ['numero_placa', 'marca', 'modelo', 'color', 'año', 'cliente', 'fecha_registro']
    list_filter = ['marca', 'modelo', 'año', 'tipo_combustible', 'fecha_registro']
    search_fields = ['numero_placa', 'vin', 'numero_motor', 'cliente__nombre', 'cliente__apellido']
    ordering = ['-fecha_registro']
    readonly_fields = ['fecha_registro']
    
    fieldsets = (
        ('Información General', {
            'fields': ('numero_placa', 'vin', 'numero_motor')
        }),
        ('Especificaciones', {
            'fields': ('marca', 'modelo', 'tipo', 'version', 'color', 'año', 'cilindrada', 'tipo_combustible')
        }),
        ('Propietario', {
            'fields': ('cliente',)
        }),
        ('Registro', {
            'fields': ('fecha_registro',),
            'classes': ('collapse',)
        }),
    )

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'nit', 'telefono', 'correo', 'contacto']
    search_fields = ['nombre', 'nit', 'correo', 'telefono', 'contacto']
    ordering = ['nombre']
    
    fieldsets = (
        ('Información General', {
            'fields': ('nombre', 'nit')
        }),
        ('Contacto', {
            'fields': ('contacto', 'telefono', 'correo')
        }),
        ('Dirección', {
            'fields': ('direccion',)
        }),
    )

admin.site.register(Area)
admin.site.register(Item)
