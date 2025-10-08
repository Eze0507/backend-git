from django.db import models

class Inventario(models.Model):
	categoria = models.CharField(max_length=100)
	codigo = models.CharField(max_length=50, unique=True)
	descripcion = models.TextField(blank=True, null=True)
	fabricante = models.CharField(max_length=100, blank=True, null=True)
	imagen = models.URLField(blank=True, null=True)
	nombre = models.CharField(max_length=100)
	precio = models.DecimalField(max_digits=10, decimal_places=2)
	stock = models.IntegerField()
	tipo = models.CharField(max_length=50)

	def __str__(self):
		return f"{self.nombre} ({self.codigo})"

