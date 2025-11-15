from django.conf import settings
from django.db import models
from personal_admin.models_saas import Tenant

class Cliente(models.Model):
    TIPO_CHOICES = (
        ('NATURAL', 'Natural'),
        ('EMPRESA', 'Empresa'),
    )

    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100, blank=True)
    nit = models.CharField(max_length=20, db_index=True)
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.CharField(max_length=200, blank=True)
    tipo_cliente = models.CharField(max_length=10, choices=TIPO_CHOICES, default='NATURAL')

    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    activo = models.BooleanField(default=True)

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='cliente'
    )
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='clientes')
    
    class Meta:
        ordering = ['-fecha_registro']
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        unique_together = ['nit', 'tenant']

    def __str__(self):
        full = f"{self.nombre} {self.apellido}".strip()
        return f"{full} – {self.nit}"


class Cita(models.Model):
    """Modelo para gestionar citas del taller"""
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
        ('completada', 'Completada'),
    ]
    
    TIPO_CITA_CHOICES = [
        ('reparacion', 'Reparación'),
        ('mantenimiento', 'Mantenimiento'),
        ('diagnostico', 'Diagnóstico'),
        ('entrega', 'Entrega'),
    ]
    
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='citas',
        verbose_name='Cliente'
    )
    
    vehiculo = models.ForeignKey(
        'operaciones_inventario.Vehiculo',
        on_delete=models.CASCADE,
        related_name='citas',
        verbose_name='Vehículo',
        null=True,
        blank=True
    )
    
    empleado = models.ForeignKey(
        'personal_admin.Empleado',
        on_delete=models.SET_NULL,
        related_name='citas',
        verbose_name='Empleado',
        null=True,
        blank=True
    )
    
    fecha_hora_inicio = models.DateTimeField(verbose_name='Fecha y Hora de Inicio')
    fecha_hora_fin = models.DateTimeField(verbose_name='Fecha y Hora de Fin')
    
    tipo_cita = models.CharField(
        max_length=20,
        choices=TIPO_CITA_CHOICES,
        default='reparacion',
        verbose_name='Tipo de Cita'
    )
    
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente',
        verbose_name='Estado'
    )
    
    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name='Descripción'
    )
    
    nota = models.TextField(
        blank=True,
        null=True,
        verbose_name='Nota'
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name='Fecha de Actualización')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='citas')
    
    class Meta:
        ordering = ['fecha_hora_inicio']
        verbose_name = 'Cita'
        verbose_name_plural = 'Citas'
        indexes = [
            models.Index(fields=['fecha_hora_inicio']),
            models.Index(fields=['estado']),
            models.Index(fields=['empleado']),
        ]
    
    def get_tipo_cita_display(self):
        return dict(self.TIPO_CITA_CHOICES).get(self.tipo_cita, self.tipo_cita)
    
    def get_estado_display(self):
        return dict(self.ESTADO_CHOICES).get(self.estado, self.estado)
    
    def __str__(self):
        cliente_nombre = f"{self.cliente.nombre} {self.cliente.apellido}".strip() if self.cliente else "Sin cliente"
        return f"Cita #{self.id} - {cliente_nombre} - {self.fecha_hora_inicio.strftime('%d/%m/%Y %H:%M') if self.fecha_hora_inicio else 'Sin fecha'}"


