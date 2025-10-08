from django.db import models

class Inventario(models.Model):
	codigo = models.CharField(max_length=50, unique=True)
	nombre = models.CharField(max_length=100)
	fabricante = models.CharField(max_length=100, blank=True, null=True)
	CATEGORIA_CHOICES = [
		("filtros", "Filtros"),
		("frenos", "Frenos"),
		("lubricantes", "Lubricantes"),
		("suspension", "Suspensión"),
		("motor", "Motor"),
		("electrico", "Eléctrico"),
		("herramientas", "Herramientas"),
		("otros", "Otros"),
	]
	categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES)
	imagen = models.URLField(blank=True, null=True)
	precio = models.DecimalField(max_digits=10, decimal_places=2)
	stock = models.IntegerField()
	descripcion = models.TextField(blank=True, null=True)	
	TIPO_CHOICES = [
		("venta", "Ítem de venta"),
		("almacen", "Ítem de almacén"),
	]
	tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)

	def __str__(self):
		return f"{self.nombre} ({self.codigo})"
