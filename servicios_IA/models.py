from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from operaciones_inventario.modelsVehiculos import Vehiculo
from personal_admin.models_saas import Tenant
class LecturaPlaca(models.Model):
    id = models.AutoField(primary_key=True)
    placa = models.CharField(max_length=20)
    score = models.FloatField()
    camera_id = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, null=True)
    match = models.BooleanField(default=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='lecturas_placa')

    class Meta:
        db_table = "lectura_placa"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.placa} ({self.score:.2f}) @ {self.created_at:%Y-%m-%d %H:%M}"


class Reporte(models.Model):
    """
    Modelo para almacenar el historial de reportes generados
    """
    TIPO_CHOICES = [
        ('ESTATICO', 'Estático'),
        ('PERSONALIZADO', 'Personalizado'),
        ('NATURAL', 'Lenguaje Natural'),
    ]
    
    FORMATO_CHOICES = [
        ('PDF', 'PDF'),
        ('XLSX', 'Excel'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reportes')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    consulta_original = models.TextField(help_text="Configuración JSON o texto de consulta")
    formato = models.CharField(max_length=10, choices=FORMATO_CHOICES)
    archivo = models.FileField(upload_to='reportes/%Y/%m/', blank=True, null=True)
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    registros_procesados = models.IntegerField(default=0)
    tiempo_generacion = models.FloatField(default=0.0, help_text="Tiempo en segundos")
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='reportes')
    
    class Meta:
        db_table = "reporte"
        ordering = ['-fecha_generacion']
        verbose_name = "Reporte"
        verbose_name_plural = "Reportes"
    
    def __str__(self):
        return f"{self.nombre} - {self.get_tipo_display()} ({self.formato}) - {self.fecha_generacion:%d/%m/%Y}"
