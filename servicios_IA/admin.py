from django.contrib import admin
from .models import LecturaPlaca, Reporte

@admin.register(LecturaPlaca)
class LecturaPlacaAdmin(admin.ModelAdmin):
    list_display = ['id', 'placa', 'score', 'match', 'vehiculo', 'camera_id', 'created_at']
    list_filter = ['match', 'created_at']
    search_fields = ['placa', 'camera_id']
    readonly_fields = ['created_at']
    ordering = ['-created_at']


@admin.register(Reporte)
class ReporteAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'tipo', 'formato', 'usuario', 'fecha_generacion', 'registros_procesados']
    list_filter = ['tipo', 'formato', 'fecha_generacion']
    search_fields = ['nombre', 'descripcion', 'usuario__username']
    readonly_fields = ['fecha_generacion', 'tiempo_generacion']
    ordering = ['-fecha_generacion']
    
    fieldsets = (
        ('Información General', {
            'fields': ('usuario', 'tipo', 'nombre', 'descripcion')
        }),
        ('Configuración', {
            'fields': ('consulta_original', 'formato')
        }),
        ('Archivo Generado', {
            'fields': ('archivo',)
        }),
        ('Métricas', {
            'fields': ('registros_procesados', 'tiempo_generacion', 'fecha_generacion')
        }),
    )
