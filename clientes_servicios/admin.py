from django.contrib import admin

# Register your models here.
#Herramienta solo de gestion no afecta en nada si lo borro
from .models import Cliente

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido', 'nit', 'correo', 'telefono', 'tipo_cliente', 'activo', 'fecha_registro')
    list_filter = ('tipo_cliente', 'activo')
    search_fields = ('nombre', 'apellido', 'nit', 'correo', 'telefono')
