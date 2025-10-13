from django.db import models
from django.contrib.auth.models import User
from operaciones_inventario.modelsArea import Area

class Cargo(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField()
    sueldo = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.nombre
    
class Empleado(models.Model):
    class Sexo(models.TextChoices):
        MASCULINO = "M", "Masculino"
        FEMENINO  = "F", "Femenino"
        OTRO      = "O", "Otro"
    cargo   = models.ForeignKey('personal_admin.Cargo', on_delete=models.CASCADE, related_name='empleados')
    usuario = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='empleado')
    area = models.ForeignKey('operaciones_inventario.Area', on_delete=models.SET_NULL, related_name='empleados',null=True, blank=True)

    nombre   = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    ci       = models.CharField(max_length=30, unique=True, verbose_name="CI")
    direccion = models.CharField(max_length=255, blank=True)
    telefono  = models.CharField(max_length=20, blank=True)
    sexo     = models.CharField(max_length=1, choices=Sexo.choices, blank=True)
    sueldo   = models.DecimalField(max_digits=10, decimal_places=2)
    estado   = models.BooleanField(default=True)

    fecha_registro    = models.DateTimeField(auto_now_add=True)
    fecha_actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "empleado"
        indexes = [
            models.Index(fields=["ci"]),
            models.Index(fields=["apellido", "nombre"]),
        ]

    def __str__(self):
        return f"{self.apellido}, {self.nombre} ({self.ci})"

class Bitacora(models.Model):
    class Accion(models.TextChoices):
        CREAR = "CREAR", "Crear"
        EDITAR = "EDITAR", "Editar"
        ELIMINAR = "ELIMINAR", "Eliminar"
        LOGIN = "LOGIN", "Iniciar Sesión"
        LOGOUT = "LOGOUT", "Cerrar Sesión"
    
    class Modulo(models.TextChoices):
        CARGO = "Cargo", "Cargo"
        CLIENTE = "Cliente", "Cliente"
        EMPLEADO = "Empleado", "Empleado"
        VEHICULO = "Vehiculo", "Vehículo"
        ITEM = "Item", "Item"
        AUTENTICACION = "Autenticacion", "Autenticación"
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bitacoras')
    accion = models.CharField(max_length=20, choices=Accion.choices)
    modulo = models.CharField(max_length=20, choices=Modulo.choices)
    descripcion = models.TextField()
    ip_address = models.GenericIPAddressField(verbose_name="Dirección IP", null=True, blank=True)
    fecha_accion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "bitacora"
        indexes = [
            models.Index(fields=["usuario"]),
            models.Index(fields=["fecha_accion"]),
            models.Index(fields=["modulo"]),
            models.Index(fields=["ip_address"]),
        ]
        ordering = ["-fecha_accion"]
    
    def __str__(self):
        ip_info = f" desde {self.ip_address}" if self.ip_address else ""
        return f"{self.usuario.username} - {self.accion} en {self.modulo}{ip_info} ({self.fecha_accion})"