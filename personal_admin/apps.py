from django.apps import AppConfig


class PersonalAdminConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'personal_admin'
    
    def ready(self):
        pass
        # import personal_admin.signals  # Comentado: el módulo signals no existe
