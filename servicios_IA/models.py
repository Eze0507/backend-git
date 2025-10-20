from django.db import models
from django.utils import timezone
from operaciones_inventario.modelsVehiculos import Vehiculo

class LecturaPlaca(models.Model):
    id = models.AutoField(primary_key=True)
    placa = models.CharField(max_length=20)
    score = models.FloatField()
    camera_id = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, null=True)
    match = models.BooleanField(default=False)

    class Meta:
        db_table = "lectura_placa"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.placa} ({self.score:.2f}) @ {self.created_at:%Y-%m-%d %H:%M}"
