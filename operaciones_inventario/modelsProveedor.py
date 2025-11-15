from django.db import models

class Proveedor(models.Model):
    contacto = models.CharField(max_length=100, null=True, blank=True)
    correo = models.EmailField(max_length=254, null=True, blank=True)
    direccion = models.CharField(max_length= 200, null=True, blank=True)
    nit = models.CharField(max_length= 25, null=True, blank=True)
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    tenant = models.ForeignKey('personal_admin.Tenant', on_delete=models.CASCADE, related_name='proveedores')
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        db_table = 'proveedor'
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        ordering = ['-id']
        unique_together = ['nombre', 'tenant']