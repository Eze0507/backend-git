from django.db import models
from personal_admin.models_saas import Tenant


class Item(models.Model):
	codigo = models.CharField(max_length=50)
	nombre = models.CharField(max_length=100)
	descripcion = models.TextField(blank=True)
	TIPO_CHOICES = [
		('Item de venta', 'Item de venta'),
		('Item de taller', 'Item de taller'),
		('Servicio', 'Servicio'),
	]
	tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
	
	fabricante = models.CharField(max_length=100,blank=True, null=True)
	precio = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
	costo = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
	stock = models.PositiveIntegerField(blank=True, null=True)
	imagen = models.URLField(blank=True, null=True)	
	ESTADO_CHOICES = [
		('Disponible', 'Disponible'),
		('No disponible', 'No disponible'),
	]
	estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='Disponible')
	area = models.ForeignKey('operaciones_inventario.Area', on_delete=models.SET_NULL, related_name='items',null=True,blank=True)
	tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='items')

	class Meta:
		unique_together = ('codigo', 'tenant')
	
	def __str__(self):
		return f"{self.nombre} ({self.codigo})"
    

