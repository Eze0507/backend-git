from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models_saas import UserProfile # Asegúrate de importar tu UserProfile

#@receiver(post_save, sender=User)
#def create_user_profile(sender, instance, created, **kwargs):
#    """
#    Crea un UserProfile automáticamente cada vez que se crea un User.
#    """
#    if created:
#        UserProfile.objects.create(usuario=instance)

#@receiver(post_save, sender=User)
#def save_user_profile(sender, instance, **kwargs):
#    """
#    Guarda el profile cada vez que el User se guarda.
#    """
#    # Se usa 'hasattr' para evitar errores si el profile aún no existe
#    if hasattr(instance, 'profile'):
#        instance.profile.save()
#    else:
#        # Si el usuario es antiguo y no tiene profile, se lo creamos
#        UserProfile.objects.create(usuario=instance)
