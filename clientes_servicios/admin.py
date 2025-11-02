from django.contrib import admin

# Register your models here.
#Herramienta solo de gestion no afecta en nada si lo borro
from .models import Cliente, Cita

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'apellido', 'get_correo', 'telefono', 'tipo_cliente')

    def get_correo(self, obj):
        return obj.usuario.email if obj.usuario else "-"
    get_correo.short_description = 'Correo'

@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ['id', 'cliente', 'vehiculo', 'empleado', 'fecha_hora_inicio', 'fecha_hora_fin', 'tipo_cita', 'estado']
    list_filter = ['estado', 'tipo_cita', 'fecha_hora_inicio', 'fecha_creacion']
    search_fields = ['cliente__nombre', 'cliente__apellido', 'vehiculo__numero_placa', 'descripcion']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    date_hierarchy = 'fecha_hora_inicio'
