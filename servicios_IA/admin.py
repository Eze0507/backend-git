from django.contrib import admin
from .models import LecturaPlaca

@admin.register(LecturaPlaca)
class LecturaPlacaAdmin(admin.ModelAdmin):
    list_display = ['id', 'placa', 'score', 'match', 'vehiculo', 'camera_id', 'created_at']
    list_filter = ['match', 'created_at']
    search_fields = ['placa', 'camera_id']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
