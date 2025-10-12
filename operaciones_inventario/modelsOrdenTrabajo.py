from django.db import models
from clientes_servicios.models import Cliente
from .modelsVehiculos import Vehiculo
from personal_admin.models import Empleado
from decimal import Decimal
from .modelsItem import Item

class OrdenTrabajo(models.Model):
    CHOICE_ESTADO = [
    ('pendiente', 'Pendiente'),
    ('en_proceso', 'En Proceso'),
    ('finalizada', 'Finalizada'),
    ('entregada', 'Entregada'),
    ('cancelada', 'Cancelada'),
    ]
    
    CHOICE_NIVEL_COMBUSTIBLE = [
        (0, 'E (Vacío)'),
        (1, '1/4'),
        (2, '1/2'),
        (3, '3/4'),
        (4, 'F (Lleno)'),
    ]
    
    id = models.AutoField(primary_key=True)
    fallo_requerimiento = models.TextField(null=True, blank=True)
    descuento = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    impuesto = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    estado = models.CharField(max_length=20, choices=CHOICE_ESTADO)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_inicio = models.DateTimeField(null=True, blank=True)
    fecha_finalizacion = models.DateTimeField(null=True, blank=True)
    fecha_entrega = models.DateTimeField(null=True, blank=True)
    kilometraje = models.IntegerField(default=0, blank=True)
    nivel_combustible = models.PositiveSmallIntegerField(choices=CHOICE_NIVEL_COMBUSTIBLE, default=0)
    observaciones = models.TextField(null=True, blank=True)
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name='ordenes')
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='ordenes')
    
    def recalcular_totales(self):
        detalles = self.detalles.all()
        total_detalles = sum([d.total for d in detalles], Decimal('0.00'))
        total_descuentos = sum([d.descuento for d in detalles], Decimal('0.00'))
        subtotal_orden = sum([d.subtotal for d in detalles], Decimal('0.00'))
        impuesto = (total_detalles) * Decimal('0.13')
        total_final = total_detalles + impuesto
        self.subtotal = subtotal_orden
        self.impuesto = impuesto
        self.descuento = total_descuentos
        self.total = total_final
        self.save(update_fields=['subtotal', 'impuesto', 'total', 'descuento'])

    def __str__(self):
        return f"Orden {self.id} - {self.estado}"
    
    class Meta:
        db_table = 'orden_trabajo'
        verbose_name = 'Orden de Trabajo'
        verbose_name_plural = 'Ordenes de Trabajo'
        ordering = ['-fecha_creacion']

class DetalleOrdenTrabajo(models.Model):
    id = models.AutoField(primary_key=True)
    orden_trabajo = models.ForeignKey(OrdenTrabajo, on_delete=models.CASCADE, related_name='detalles')
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    descuento = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='detalles_orden', null=True, blank=True)
    item_personalizado = models.CharField(max_length=200, null=True, blank=True)
    
    def save(self, *args, **kwargs):
        self.subtotal = Decimal(self.precio_unitario) * Decimal(self.cantidad)
        self.total = self.subtotal - Decimal(self.descuento)
        if self.total < 0:
            self.total = Decimal('0.00')
        super().save(*args, **kwargs)
        self.orden_trabajo.recalcular_totales()
    
    def delete(self, *args, **kwargs):
        orden = self.orden_trabajo
        super().delete(*args, **kwargs)
        orden.recalcular_totales()
    
    def __str__(self):
        return f"Detalle {self.id} de Orden {self.orden_trabajo.id}"
    
    @property
    def nombre_item(self):
        """Devuelve el nombre del item, ya sea del catálogo o personalizado"""
        if self.item:
            return self.item.nombre
        return self.item_personalizado or "Sin especificar"
    
    def clean(self):
        """Validar que se proporcione al menos uno de los dos campos"""
        from django.core.exceptions import ValidationError
        if not self.item and not self.item_personalizado:
            raise ValidationError("Debe seleccionar un item del catálogo o especificar un item personalizado")
        
        if self.item and self.item_personalizado:
            raise ValidationError("No puede seleccionar un item del catálogo Y especificar uno personalizado")
    
    class Meta:
        db_table = 'detalle_orden_trabajo'
        verbose_name = 'Detalle de Orden de Trabajo'
        verbose_name_plural = 'Detalles de Ordenes de Trabajo'
        ordering = ['id']

class InventarioVehiculo (models.Model):
    id = models.AutoField(primary_key=True)
    orden_trabajo = models.ForeignKey(OrdenTrabajo, on_delete=models.CASCADE, related_name='inventario_vehiculo')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='inventario_vehiculo', null=True, blank=True)
    
    def __str__(self):
        return f"Inventario de Vehiculo {self.id} - Orden {self.orden_trabajo.id}"
    class Meta:
        db_table = 'inventario_vehiculo'
        verbose_name = 'Inventario de Vehiculo'
        verbose_name_plural = 'Inventarios de Vehiculos'
        ordering = ['id']

class ItemInventarioVehiculo(models.Model):
    id = models.AutoField(primary_key=True)
    inventario_vehiculo = models.ForeignKey(InventarioVehiculo, on_delete=models.CASCADE, related_name='items')
    extintor = models.BooleanField(default=False)
    botiquin = models.BooleanField(default=False)
    antena = models.BooleanField(default=False)
    llanta_repuesto = models.BooleanField(default=False)
    documentos = models.BooleanField(default=False)
    encendedor = models.BooleanField(default=False)
    pisos = models.BooleanField(default=False)
    luces = models.BooleanField(default=False)
    llaves = models.BooleanField(default=False)
    gata = models.BooleanField(default=False)
    herramientas = models.BooleanField(default=False)
    tapas_ruedas = models.BooleanField(default=False)
    triangulos = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Item {self.id} de Inventario de Vehiculo"
    
    class Meta:
        db_table = 'item_inventario_vehiculo'
        verbose_name = 'Item de Inventario de Vehiculo'
        verbose_name_plural = 'Items de Inventarios de Vehiculos'
        ordering = ['id']

class TareaOrdenTrabajo(models.Model):
    id = models.AutoField(primary_key=True)
    orden_trabajo = models.ForeignKey(OrdenTrabajo, on_delete=models.CASCADE, related_name='tareas')
    descripcion = models.CharField(max_length=200)
    completada = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Tarea {self.id} de Orden {self.orden_trabajo.id}"
    
    class Meta:
        db_table = 'tareas_orden_trabajo'
        verbose_name = 'Tarea de Orden de Trabajo'
        verbose_name_plural = 'Tareas de Ordenes de Trabajo'
        ordering = ['id']

class ImagenOrdenTrabajo(models.Model):
    id = models.AutoField(primary_key=True)
    orden_trabajo = models.ForeignKey(OrdenTrabajo, on_delete=models.CASCADE, related_name='imagenes')
    imagen_url = models.URLField(blank=True, null=True)
    descripcion = models.CharField(max_length=200, blank=True)
    
    def __str__(self):
        return f"Imagen {self.id} de Orden {self.orden_trabajo.id}"
    
    class Meta:
        db_table = 'imagenes_orden_trabajo'
        verbose_name = 'Imagen de Orden de Trabajo'
        verbose_name_plural = 'Imagenes de Ordenes de Trabajo'
        ordering = ['id']

class PruebaRuta(models.Model):
    CHOICE_TIPO_PRUEBA = [
        ('inicial', 'Inicial'),
        ('intermedio', 'Intermedio'),
        ('final', 'Final'),
    ]
    
    CHOICE_ESTADO = [
        ('bueno', 'Bueno'),
        ('regular', 'Regular'),
        ('malo', 'Malo'),
    ]
    
    id = models.AutoField(primary_key=True)
    orden_trabajo = models.ForeignKey(OrdenTrabajo, on_delete=models.CASCADE, related_name='pruebas_ruta')
    fecha_prueba = models.DateTimeField(auto_now_add=True)
    tipo_prueba = models.CharField(max_length=20, choices=CHOICE_TIPO_PRUEBA)
    kilometraje_inicio = models.IntegerField(null=True, blank=True)
    kilometraje_final = models.IntegerField(null=True, blank=True)
    ruta = models.TextField()
    frenos = models.CharField(choices=CHOICE_ESTADO, max_length=20)
    motor = models.CharField(choices=CHOICE_ESTADO, max_length=20)
    suspension = models.CharField(choices=CHOICE_ESTADO, max_length=20)
    direccion = models.CharField(choices=CHOICE_ESTADO, max_length=20)
    observaciones = models.TextField()
    tecnico = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, related_name='pruebas_ruta')
    
    def __str__(self):
        return f"Prueba de Ruta {self.id} de Orden {self.orden_trabajo.id}"
    
    class Meta:
        db_table = 'pruebas_ruta'
        verbose_name = 'Prueba de Ruta'
        verbose_name_plural = 'Pruebas de Ruta'
        ordering = ['id']

class NotaOrdenTrabajo(models.Model):
    id = models.AutoField(primary_key=True)
    orden_trabajo = models.ForeignKey(OrdenTrabajo, on_delete=models.CASCADE, related_name='notas')
    fecha_nota = models.DateTimeField(auto_now_add=True)
    contenido = models.TextField()
    
    def __str__(self):
        return f"Nota {self.id} de Orden {self.orden_trabajo.id}"
    
    class Meta:
        db_table = 'nota_orden_trabajo'
        verbose_name = 'Nota de Orden de Trabajo'
        verbose_name_plural = 'Notas de Ordenes de Trabajo'
        ordering = ['id']

class Inspeccion(models.Model):
    TIPO_INSPECCION = [
        ('ingreso', 'Ingreso'),
        ('salida', 'Salida'),
    ]
    id = models.AutoField(primary_key=True)
    orden_trabajo = models.ForeignKey('OrdenTrabajo', on_delete=models.CASCADE, related_name='inspecciones')
    tipo_inspeccion = models.CharField(max_length=20, choices=TIPO_INSPECCION)
    fecha = models.DateTimeField(auto_now_add=True)
    tecnico = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, related_name='inspecciones')
    observaciones_generales = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Inspección {self.tipo_inspeccion} - Orden {self.orden_trabajo.id}"
    
    class Meta:
        db_table = 'inspeccion'
        verbose_name = 'Inspección'
        verbose_name_plural = 'Inspecciones'

class DetalleInspeccion(models.Model):
    OPCIONES_ESTADO = [
        ('bueno', 'Buen estado'),
        ('malo', 'Mal estado'),
    ]
    
    OPCIONES_NIVEL = [
        ('alto', 'Alto'),
        ('medio', 'Medio'),
        ('bajo', 'Bajo'),
    ]
    
    id = models.AutoField(primary_key=True)
    inspeccion = models.ForeignKey(Inspeccion, on_delete=models.CASCADE, related_name='detalles')
    aceite_motor = models.CharField(max_length=20, choices=OPCIONES_ESTADO, blank=True, null=True)
    Filtros_VH = models.CharField(max_length=20, choices=OPCIONES_ESTADO, blank=True, null=True)
    nivel_refrigerante = models.CharField(max_length=20, choices=OPCIONES_NIVEL, blank=True, null=True)
    pastillas_freno = models.CharField(max_length=20, choices=OPCIONES_ESTADO, blank=True, null=True)
    Estado_neumaticos = models.CharField(max_length=20, choices=OPCIONES_ESTADO, blank=True, null=True)
    estado_bateria = models.CharField(max_length=20, choices=OPCIONES_NIVEL, blank=True, null=True)
    estado_luces = models.CharField(max_length=20, choices=OPCIONES_ESTADO, blank=True, null=True)
    
    def __str__(self):
        return f"Detalle de Inspección {self.id} - Inspección {self.inspeccion.id}"
    
    class Meta:
        db_table = 'detalle_inspeccion'
        verbose_name = 'Detalle de Inspección'
        verbose_name_plural = 'Detalles de Inspección'

class AsignacionTecnico(models.Model):
    id = models.AutoField(primary_key=True)
    orden_trabajo = models.ForeignKey(OrdenTrabajo, on_delete=models.CASCADE, related_name='asignaciones_tecnicos')
    tecnico = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, related_name='asignaciones_tecnicos')
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Técnico {self.tecnico} asignado a Orden {self.orden_trabajo.id}"
    
    class Meta:
        db_table = 'asignacion_tecnico'
        verbose_name = 'Asignación de Técnico'
        verbose_name_plural = 'Asignaciones de Técnicos'
        ordering = ['id']
