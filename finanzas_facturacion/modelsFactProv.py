from django.db import models
from operaciones_inventario.modelsProveedor import Proveedor

class FacturaProveedor(models.Model):
    id = models.AutoField(primary_key=True)
    numero = models.CharField(max_length=50)
    fecha_registro = models.DateField()
    observacion = models.TextField(blank=True, null=True)
    descuento_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Porcentaje de descuento (0-100)")
    impuesto_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Porcentaje de IVA (0-100)")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Monto calculado del descuento")
    impuesto = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Monto calculado del IVA")
    total = models.DecimalField(max_digits=10, decimal_places=2)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name='facturas_proveedor')
    class Meta:
        db_table = 'factura_proveedor'
        verbose_name = 'Factura de Proveedor'
        verbose_name_plural = 'Facturas de Proveedor'
        ordering = ['id']

    def calcular_montos(self):
        """Calcula descuento, impuesto y total basado en porcentajes"""
        # Calcular descuento en monto
        self.descuento = (self.subtotal * self.descuento_porcentaje) / 100
        
        # Calcular base imponible (subtotal - descuento)
        base_imponible = self.subtotal - self.descuento
        
        # Calcular impuesto en monto
        self.impuesto = (base_imponible * self.impuesto_porcentaje) / 100
        
        # Calcular total
        self.total = base_imponible + self.impuesto

    def save(self, *args, **kwargs):
        """Sobreescribir save para calcular automáticamente"""
        self.calcular_montos()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Factura {self.numero}"
