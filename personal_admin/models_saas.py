from django.db import models
from django.contrib.auth.models import User
import string
import random

class Tenant(models.Model):
    nombre_taller = models.CharField(max_length=100, unique=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    propietario = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='taller_propietario', null=True, blank=True)
    ubicacion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    horarios = models.TextField(blank=True, null=True, help_text="Ej: Lunes a Viernes 8:00-18:00, Sábado 9:00-14:00")
    email_contacto = models.EmailField(blank=True, null=True)
    logo = models.URLField(blank=True, null=True)
    codigo_invitacion = models.CharField(max_length=50, blank=True, null=True, unique=True, help_text="Código único para invitar usuarios al taller")
    
    def __str__(self):
        return self.nombre_taller
    
    def save(self, *args, **kwargs):
        if not self.codigo_invitacion:
            codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            while Tenant.objects.filter(codigo_invitacion=codigo).exists():
                codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            self.codigo_invitacion = codigo
        super().save(*args, **kwargs)
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