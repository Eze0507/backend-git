from django.db import models
from django.contrib.auth.models import User

class Tenant(models.Model):
    nombre_taller = models.CharField(max_length=100, unique=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.nombre_taller
    
    class Meta:
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"

class UserProfile(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='user_profiles')
    
    def __str__(self):
        return f"{self.usuario.username} - {self.tenant.nombre_taller}"
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"