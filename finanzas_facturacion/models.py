from django.db import models
from operaciones_inventario.modelsOrdenTrabajo import OrdenTrabajo
from django.contrib.auth.models import User
from personal_admin.models_saas import Tenant


class Pago(models.Model):
    """
    Modelo para gestionar los pagos de las órdenes de trabajo.
    Soporta múltiples métodos de pago incluyendo Stripe.
    """
    
    METODO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta'),
        ('transferencia', 'Transferencia Bancaria'),
        ('stripe', 'Stripe'),
        ('otro', 'Otro'),
    ]
    
    ESTADO_PAGO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('procesando', 'Procesando'),
        ('completado', 'Completado'),
        ('fallido', 'Fallido'),
        ('reembolsado', 'Reembolsado'),
        ('cancelado', 'Cancelado'),
    ]
    
    id = models.AutoField(primary_key=True)
    orden_trabajo = models.ForeignKey(
        OrdenTrabajo, 
        on_delete=models.CASCADE, 
        related_name='pagos',
        verbose_name='Orden de Trabajo'
    )
    monto = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name='Monto'
    )
    metodo_pago = models.CharField(
        max_length=20, 
        choices=METODO_PAGO_CHOICES,
        default='efectivo',
        verbose_name='Método de Pago'
    )
    estado = models.CharField(
        max_length=20, 
        choices=ESTADO_PAGO_CHOICES, 
        default='pendiente',
        verbose_name='Estado del Pago'
    )
    fecha_pago = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Pago'
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )
    
    # Campos específicos de Stripe
    stripe_payment_intent_id = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        verbose_name='Payment Intent ID de Stripe',
        help_text='ID del Payment Intent creado en Stripe'
    )
    currency = models.CharField(
        max_length=10, 
        default='bob',
        verbose_name='Moneda',
        help_text='Código de moneda (bob, usd, etc.)'
    )
    
    # Información adicional
    descripcion = models.TextField(
        blank=True, 
        null=True,
        default='Pago de servicio de taller',
        verbose_name='Descripción'
    )
    numero_referencia = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name='Número de Referencia'
    )
    
    # Usuario que registró el pago
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Usuario que registró'
    )
    tenant = models.ForeignKey('personal_admin.Tenant', on_delete=models.CASCADE, related_name='pagos')
    
    def __str__(self):
        return f"Pago #{self.id} - Orden #{self.orden_trabajo.id} - {self.estado}"
    
    class Meta:
        db_table = 'pagos'
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'
        ordering = ['-fecha_pago']
        indexes = [
            models.Index(fields=['orden_trabajo', 'estado']),
            models.Index(fields=['fecha_pago']),
            models.Index(fields=['stripe_payment_intent_id']),
        ]
    
    def es_completado(self):
        """Verifica si el pago fue completado"""
        return self.estado == 'completado'
    
    def puede_reembolsar(self):
        """Verifica si el pago puede ser reembolsado"""
        return self.estado == 'completado' and self.metodo_pago == 'stripe'
