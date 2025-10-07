from django.db import models


class Area(models.Model):
    """
    Modelo para representar las áreas de servicios del taller.
    Ejemplo: Mecánica, Electricidad, Carrocería
    """
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre del Área")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de Actualización")

    class Meta:
        ordering = ["nombre"]
        indexes = [
            models.Index(fields=["nombre"]),
            models.Index(fields=["activo"])
        ]
        verbose_name = "Área"
        verbose_name_plural = "Áreas"

    def __str__(self):
        return self.nombre


class Categoria(models.Model):
    """
    Modelo para representar las categorías dentro de cada área.
    Ejemplo: Mantenimiento, Motor, Suspensión (dentro de Mecánica)
    """
    area = models.ForeignKey(
        'Area', 
        on_delete=models.CASCADE, 
        related_name='categorias',
        verbose_name="Área"
    )
    nombre = models.CharField(max_length=100, verbose_name="Nombre de la Categoría")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de Actualización")

    class Meta:
        unique_together = ("area", "nombre")
        ordering = ["area__nombre", "nombre"]
        indexes = [
            models.Index(fields=["area"]),
            models.Index(fields=["nombre"]),
            models.Index(fields=["activo"])
        ]
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"

    def __str__(self):
        return f"{self.nombre} ({self.area.nombre})"


class Servicio(models.Model):
    """
    Modelo para representar los servicios específicos que ofrece el taller.
    Ejemplo: Cambio de aceite, Alineación, Diagnóstico eléctrico
    """
    categoria = models.ForeignKey(
        'Categoria', 
        on_delete=models.CASCADE, 
        related_name='servicios',
        verbose_name="Categoría"
    )
    nombre = models.CharField(max_length=150, verbose_name="Nombre del Servicio")
    descripcion = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Descripción",
        help_text="Descripción detallada del servicio"
    )
    precio = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Precio",
        help_text="Precio base del servicio en bolivianos"
    )
    activo = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de Actualización")

    class Meta:
        unique_together = ("categoria", "nombre")
        ordering = ["categoria__area__nombre", "categoria__nombre", "nombre"]
        indexes = [
            models.Index(fields=["categoria"]),
            models.Index(fields=["nombre"]),
            models.Index(fields=["activo"]),
            models.Index(fields=["precio"])
        ]
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"

    def __str__(self):
        return f"{self.nombre} - {self.categoria.nombre}"

    def clean(self):
        """
        Validación a nivel de modelo para asegurar consistencia de datos
        """
        from django.core.exceptions import ValidationError
        
        # No permitir precio negativo
        if self.precio < 0:
            raise ValidationError("El precio no puede ser negativo")
        
        # No permitir activar servicio si la categoría está inactiva
        if self.activo and not self.categoria.activo:
            raise ValidationError("No se puede activar un servicio si su categoría está inactiva")
        
        # No permitir activar servicio si el área está inactiva
        if self.activo and not self.categoria.area.activo:
            raise ValidationError("No se puede activar un servicio si su área está inactiva")
