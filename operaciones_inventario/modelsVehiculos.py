from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from clientes_servicios.models import Cliente
from personal_admin.models_saas import Tenant


class Marca(models.Model):
    """Modelo para las marcas de vehículos"""
    nombre = models.CharField(max_length=80, null=False, blank=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='marcas_vehiculos')
    
    class Meta:
        unique_together = ['nombre', 'tenant']
        ordering = ['nombre']
        verbose_name = 'Marca'
        verbose_name_plural = 'Marcas'
    
    def __str__(self):
        return self.nombre


class Modelo(models.Model):
    """Modelo para los modelos de vehículos"""
    marca = models.ForeignKey(
        Marca,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='modelos'
    )
    nombre = models.CharField(max_length=80, null=False, blank=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='modelos_vehiculos')
    
    class Meta:
        ordering = ['marca__nombre', 'nombre']
        verbose_name = 'Modelo'
        verbose_name_plural = 'Modelos'
        unique_together = ['nombre', 'marca', 'tenant']
    
    def __str__(self):
        if self.marca:
            return f"{self.marca.nombre} {self.nombre}"
        return self.nombre


class Vehiculo(models.Model):
    """Modelo para los vehículos"""
    
    # Choices para el tipo de vehículo
    TIPO_CHOICES = [
        ('CAMIONETA', 'Camioneta'),
        ('DEPORTIVO', 'Deportivo'),
        ('FURGON', 'Furgón'),
        ('HATCHBACK', 'Hatchback'),
        ('SEDAN', 'Sedán'),
        ('SUV', 'SUV'),
        ('CITYCAR', 'CityCar'),
    ]
    
    cliente = models.ForeignKey(
        Cliente, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='vehiculos'
    )
    marca = models.ForeignKey(
        Marca, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='vehiculos'
    )
    modelo = models.ForeignKey(
        Modelo, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='vehiculos'
    )
    
    # Campos del vehículo
    vin = models.CharField(max_length=40, blank=True, null=True, verbose_name='VIN')
    numero_motor = models.CharField(max_length=40, blank=True, null=True, verbose_name='Número de Motor')
    numero_placa = models.CharField(
        max_length=20,  
        null=False, 
        blank=False,
        verbose_name='Número de Placa',
        error_messages={
            'unique': 'Ya existe un vehículo con este número de placa.',
            'blank': 'El número de placa es obligatorio.',
            'null': 'El número de placa es obligatorio.',
        }
    )
    tipo = models.CharField(
        max_length=20, 
        choices=TIPO_CHOICES, 
        blank=True, 
        null=True,
        verbose_name='Tipo de Vehículo'
    )
    version = models.CharField(max_length=40, blank=True, null=True, verbose_name='Versión')
    color = models.CharField(max_length=30, blank=True, null=True)
    año = models.SmallIntegerField(
        validators=[
            MinValueValidator(1950),
            MaxValueValidator(2100)
        ],
        null=True,
        blank=True,
        verbose_name='Año'
    )
    cilindrada = models.IntegerField(null=True, blank=True)
    tipo_combustible = models.CharField(max_length=40, blank=True, null=True, verbose_name='Tipo de Combustible')
    
    # Campos de auditoría
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Registro')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='vehiculos')
    
    class Meta:
        ordering = ['-fecha_registro']
        verbose_name = 'Vehículo'
        verbose_name_plural = 'Vehículos'
        unique_together = ['numero_placa', 'tenant']
    
    def __str__(self):
        marca_nombre = self.marca.nombre if self.marca else 'Sin marca'
        modelo_nombre = self.modelo.nombre if self.modelo else 'Sin modelo'
        return f"{marca_nombre} {modelo_nombre} - {self.numero_placa}"
    
