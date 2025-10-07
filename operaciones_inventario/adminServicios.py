from django.contrib import admin
from .modelsServicios import Area, Categoria, Servicio


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Area
    """
    list_display = ("id", "nombre", "activo", "created_at")
    list_display_links = ("id", "nombre")
    search_fields = ("nombre",)
    list_filter = ("activo", "created_at")
    ordering = ("nombre",)
    readonly_fields = ("created_at", "updated_at")
    
    fieldsets = (
        ("Información Básica", {
            "fields": ("nombre", "activo")
        }),
        ("Fechas", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Categoria
    """
    list_display = ("id", "nombre", "area", "activo", "created_at")
    list_display_links = ("id", "nombre")
    search_fields = ("nombre", "area__nombre")
    list_filter = ("activo", "area", "created_at")
    ordering = ("area__nombre", "nombre")
    readonly_fields = ("created_at", "updated_at")
    
    fieldsets = (
        ("Información Básica", {
            "fields": ("area", "nombre", "activo")
        }),
        ("Fechas", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Servicio
    """
    list_display = ("id", "nombre", "categoria", "precio", "activo", "created_at")
    list_display_links = ("id", "nombre")
    search_fields = ("nombre", "descripcion", "categoria__nombre", "categoria__area__nombre")
    list_filter = ("activo", "categoria", "categoria__area", "created_at")
    ordering = ("categoria__area__nombre", "categoria__nombre", "nombre")
    readonly_fields = ("created_at", "updated_at")
    
    fieldsets = (
        ("Información Básica", {
            "fields": ("categoria", "nombre", "descripcion", "precio", "activo")
        }),
        ("Fechas", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    def get_queryset(self, request):
        """
        Optimizar consultas con select_related
        """
        return super().get_queryset(request).select_related("categoria", "categoria__area")
