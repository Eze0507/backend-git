from django.contrib import admin
from .models import Empleado, Cargo


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'apellido', 'ci', 'cargo', 'area', 'estado')
    search_fields = ('nombre', 'apellido', 'ci')
    list_filter = ('cargo', 'area', 'estado')

@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'sueldo')
    search_fields = ('nombre',)

