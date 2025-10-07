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
        ordering = ["area__nombre", "nombre"]
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
        help_text="Descripción del servicio"
    )
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Precio"
    )
    activo = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de Actualización")

    class Meta:
        ordering = ["categoria__area__nombre", "categoria__nombre", "nombre"]
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"

    def __str__(self):
        return f"{self.nombre} - {self.categoria.nombre}"
