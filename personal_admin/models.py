from django.db import models
from django.contrib.auth.models import User

class Cargo(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField()
    sueldo = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.nombre
    
class Empleado(models.Model):
    class Sexo(models.TextChoices):
        MASCULINO = "M", "Masculino"
        FEMENINO  = "F", "Femenino"
        OTRO      = "O", "Otro"

    cargo   = models.ForeignKey('personal_admin.Cargo', on_delete=models.CASCADE, related_name='empleados')
    usuario = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='empleado')

    nombre   = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    ci       = models.CharField(max_length=30, unique=True, verbose_name="CI")
    direccion = models.CharField(max_length=255, blank=True)
    telefono  = models.CharField(max_length=20, blank=True)
    sexo     = models.CharField(max_length=1, choices=Sexo.choices, blank=True)
    sueldo   = models.DecimalField(max_digits=10, decimal_places=2)
    estado   = models.BooleanField(default=True)

    fecha_registro    = models.DateTimeField(auto_now_add=True)
    fecha_actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "empleado"
        indexes = [
            models.Index(fields=["ci"]),
            models.Index(fields=["apellido", "nombre"]),
        ]

    def __str__(self):
        return f"{self.apellido}, {self.nombre} ({self.ci})"