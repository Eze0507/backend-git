from django.apps import AppConfig


class OperacionesInventarioConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'operaciones_inventario'
    
    def ready(self):
        """
        Importar los modelos y admin cuando la app esté lista
        """
        import operaciones_inventario.modelsServicios
        import operaciones_inventario.adminServicios