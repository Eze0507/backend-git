from django.contrib import admin
from .models import Empleado, Cargo
from .models_saas import Tenant, UserProfile

@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'apellido', 'ci', 'cargo', 'area', 'estado')
    search_fields = ('nombre', 'apellido', 'ci')
    list_filter = ('cargo', 'area', 'estado')

@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'sueldo')
    search_fields = ('nombre',)

admin.site.register(Tenant)
admin.site.register(UserProfile)
# Register your models here.
