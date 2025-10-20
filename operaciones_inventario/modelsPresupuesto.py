from  django.db import models
from decimal import Decimal
from .modelsItem import Item as item
from .modelsVehiculos import Vehiculo
from clientes_servicios.models import Cliente
from django.core.validators import MinValueValidator, MaxValueValidator

class presupuesto(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('cancelado', 'Cancelado'),
    ]
    
    id = models.AutoField(primary_key=True)
    diagnostico = models.TextField(null=True, blank=True)
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True, related_name='presupuestos')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    # Flag para indicar si este presupuesto aplica impuestos o no (opcional para el cliente)
    con_impuestos = models.BooleanField(default=False)
    impuestos = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_descuentos = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2, default=Decimal('0.00'))
    subtotal = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2)
    total = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2)
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.SET_NULL, null=True, blank=True, related_name='presupuestos')

    class Meta:
        ordering = ['id']
        verbose_name = 'Presupuesto'
        verbose_name_plural = 'Presupuestos'
        
    def __str__(self):
        return f'Presupuesto {self.id} - Total: {self.total}'

    def recalcular_totales(self):
        detalles = self.detalles.all()
        total_detalles = sum((d.total or Decimal('0.00')) for d in detalles)
        total_descuentos = sum((getattr(d, 'descuento', Decimal('0.00')) or Decimal('0.00')) for d in detalles)
        subtotal_orden = sum((getattr(d, 'subtotal', None) or Decimal('0.00')) for d in detalles)
        
        # Calcular impuesto solo si con_impuestos está activado
        if self.con_impuestos and self.impuestos and self.impuestos > Decimal('0.00'):
            # Si el valor es menor a 1, tratarlo como decimal (0.13 = 13%)
            # Si es mayor a 1, tratarlo como porcentaje (13 = 13%)
            if self.impuestos <= Decimal('1.00'):
                tasa_impuesto = self.impuestos  # Ya es decimal (0.13)
            else:
                tasa_impuesto = self.impuestos / Decimal('100')  # Convertir porcentaje a decimal (13 -> 0.13)
            
            # Calcular impuesto sobre total_detalles (después de descuentos)
            impuesto_calculado = (total_detalles * tasa_impuesto).quantize(Decimal('0.01'))
        else:
            impuesto_calculado = Decimal('0.00')
        
        total_final = (total_detalles + impuesto_calculado).quantize(Decimal('0.01'))
        
        self.subtotal = subtotal_orden if subtotal_orden is not None else total_detalles
        self.total_descuentos = total_descuentos
        self.total = total_final
        
        # Guardar todos los campos calculados
        self.save(update_fields=['subtotal', 'total', 'total_descuentos'])
    
class detallePresupuesto(models.Model):
    id = models.AutoField(primary_key=True)
    presupuesto = models.ForeignKey(presupuesto, on_delete=models.CASCADE, related_name='detalles')
    item = models.ForeignKey(item, on_delete=models.CASCADE, related_name='detalles')
    cantidad = models.IntegerField(null=True, blank=True)
    precio_unitario = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2)
    descuento_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, validators=[MinValueValidator(0), MaxValueValidator(100)])
    subtotal = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2)
    total = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2)

    class Meta:
        ordering = ['id']
        verbose_name = 'Detalle de Presupuesto'
        verbose_name_plural = 'Detalles de Presupuestos'
        
    def __str__(self):
        return f'Detalle {self.id} del Presupuesto {self.presupuesto.id}'

    def save(self, *args, **kwargs):
        from decimal import Decimal, ROUND_HALF_UP
        
        # Calcular subtotal
        cantidad = Decimal(self.cantidad or 0)
        precio = Decimal(self.precio_unitario or Decimal('0.00'))
        self.subtotal = (precio * cantidad).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Calcular descuento basado en porcentaje (si existe) o usar 0
        if Decimal(self.descuento_porcentaje) > 0:
            descuento_calculado = (self.subtotal * (Decimal(self.descuento_porcentaje) / Decimal('100'))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        else:
            descuento_calculado = Decimal('0.00')

        # No permitir que el descuento supere el subtotal
        if descuento_calculado > self.subtotal:
            descuento_calculado = self.subtotal

        # Calcular total final
        self.total = (self.subtotal - descuento_calculado).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        if self.total < Decimal('0.00'):
            self.total = Decimal('0.00')
            
        super().save(*args, **kwargs)
        # Recalcular totales del presupuesto padre
        if self.presupuesto:
            try:
                self.presupuesto.recalcular_totales()
            except Exception:
                # Evitar que errores en recalculo rompan el guardado; se puede loggear aquí
                pass

    @property
    def descuento(self):
        """Propiedad computada: devuelve el monto de descuento según el porcentaje aplicado."""
        from decimal import Decimal, ROUND_HALF_UP
        if Decimal(self.descuento_porcentaje) > 0:
            return ( (Decimal(self.subtotal or 0) * (Decimal(self.descuento_porcentaje) / Decimal('100'))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) )
        return Decimal('0.00')

    def delete(self, *args, **kwargs):
        presupuesto_parent = self.presupuesto
        super().delete(*args, **kwargs)
        if presupuesto_parent:
            try:
                presupuesto_parent.recalcular_totales()
            except Exception:
                pass