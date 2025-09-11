
# Create your models here.
from django.db import models

class Cliente(models.Model):
    TIPO_CHOICES = (
        ('NATURAL', 'Natural'),
        ('EMPRESA', 'Empresa'),
    )

    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100, blank=True)
    nit = models.CharField(max_length=20, unique=True, db_index=True)
    correo = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.CharField(max_length=200, blank=True)
    tipo_cliente = models.CharField(max_length=10, choices=TIPO_CHOICES, default='NATURAL')

    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    # Borrado lógico para no perder histórico
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['-fecha_registro']
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    def __str__(self):
        full = f"{self.nombre} {self.apellido}".strip()
        return f"{full} – {self.nit}"

