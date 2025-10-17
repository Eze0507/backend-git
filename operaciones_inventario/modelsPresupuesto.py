from  django.db import models
from decimal import Decimal
from .modelsItem import Item as item
from .modelsVehiculos import Vehiculo

class presupuesto(models.Model):
    id = models.AutoField(primary_key=True)
    diagnostico = models.TextField(null=True, blank=True)
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)
    descuento = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2, default=Decimal('0.00'))
    # Flag para indicar si este presupuesto aplica impuestos o no (opcional para el cliente)
    con_impuestos = models.BooleanField(default=False)
    impuestos = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2, default=Decimal('0.00'))
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
        # Si cada detalle tiene un campo descuento/subtotal, ajústalo aquí. Por ahora usamos total y subtotal calculado
        subtotal_orden = sum((getattr(d, 'subtotal', None) or Decimal('0.00')) for d in detalles)
        # Si el cliente NO quiere impuestos, los ignoramos (tasa 0). Si quiere, tomamos
        # la tasa guardada en `impuestos` o usamos 13% por defecto cuando no se especificó.
        if self.con_impuestos:
            tasa_impuesto = (self.impuestos if self.impuestos not in (None, Decimal('0.00')) else Decimal('0.13'))
        else:
            tasa_impuesto = Decimal('0.00')

        impuesto = (total_detalles * tasa_impuesto).quantize(Decimal('0.01'))
        total_final = (total_detalles + impuesto).quantize(Decimal('0.01'))
        descuento = sum((getattr(d, 'descuento', None) or Decimal('0.00')) for d in detalles)
        self.subtotal = subtotal_orden if subtotal_orden is not None else total_detalles
        # Si aplican impuestos, persistimos la tasa; si no, dejar impuestos como está (o 0)
        if self.con_impuestos:
            self.impuestos = tasa_impuesto
            self.total = total_final
            self.save(update_fields=['subtotal', 'impuestos', 'total'])
        else:
            # No persistimos la tasa en 'impuestos' para mantenerla tal cual ingresada; solo actualizamos subtotal y total
            self.total = total_final
            self.save(update_fields=['subtotal', 'total'])
    
class detallePresupuesto(models.Model):
    id = models.AutoField(primary_key=True)
    presupuesto = models.ForeignKey(presupuesto, on_delete=models.CASCADE, related_name='detalles')
    item = models.ForeignKey(item, on_delete=models.CASCADE, related_name='detalles')
    cantidad = models.IntegerField(null=True, blank=True)
    precio_unitario = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2)
    descuento = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2, default=Decimal('0.00'))
    subtotal = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2)
    total = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2)

    class Meta:
        ordering = ['id']
        verbose_name = 'Detalle de Presupuesto'
        verbose_name_plural = 'Detalles de Presupuestos'
        
    def __str__(self):
        return f'Detalle {self.id} del Presupuesto {self.presupuesto.id}'

    def save(self, *args, **kwargs):
        # Asegurarnos de operar con Decimal y valores por defecto
        cantidad = Decimal(self.cantidad or 0)
        precio = Decimal(self.precio_unitario or Decimal('0.00'))
        descuento = Decimal(self.descuento or Decimal('0.00'))
        self.subtotal = (precio * cantidad).quantize(Decimal('0.01'))
        self.total = (self.subtotal - descuento)
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

    def delete(self, *args, **kwargs):
        presupuesto_parent = self.presupuesto
        super().delete(*args, **kwargs)
        if presupuesto_parent:
            try:
                presupuesto_parent.recalcular_totales()
            except Exception:
                pass