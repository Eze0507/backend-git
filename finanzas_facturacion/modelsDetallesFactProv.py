from django.db import models
from .modelsFactProv import FacturaProveedor
from operaciones_inventario.modelsItem import Item

class DetalleFacturaProveedor(models.Model):
    id = models.AutoField(primary_key=True)
    factura = models.ForeignKey(FacturaProveedor, on_delete=models.CASCADE, related_name='detalles')
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name='detalles_factura')
    cantidad = models.PositiveIntegerField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    tenant = models.ForeignKey('personal_admin.Tenant', on_delete=models.CASCADE, related_name='detalles_factura_proveedor')
    
    class Meta:
        db_table = 'detalle_factura_proveedor'
        verbose_name = 'Detalle de Factura de Proveedor'
        verbose_name_plural = 'Detalles de Factura de Proveedor'
        ordering = ['id']

    def save(self, *args, **kwargs):
        """Guardar el detalle y actualizar la factura"""
        super().save(*args, **kwargs)
        
        # Recalcular el subtotal de la factura desde los detalles
        self.factura.recalcular_desde_detalles()
        self.factura.save()

    def delete(self, *args, **kwargs):
        """Eliminar el detalle y actualizar la factura"""
        factura = self.factura
        super().delete(*args, **kwargs)
        
        # Recalcular el subtotal de la factura desde los detalles restantes
        factura.recalcular_desde_detalles()
        factura.save()

    def __str__(self):
        return f"Detalle {self.id} - {self.item.nombre} ({self.factura.numero})"