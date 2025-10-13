from django.contrib import admin

# Register your models here.
#Herramienta solo de gestion no afecta en nada si lo borro
from .models import Cliente

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'apellido', 'get_correo', 'telefono', 'tipo_cliente')

    def get_correo(self, obj):
        return obj.usuario.email if obj.usuario else "-"
    get_correo.short_description = 'Correo'
