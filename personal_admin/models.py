from django.db import models
from django.contrib.auth.models import User
from operaciones_inventario.modelsArea import Area
from .models_saas import Tenant

class Cargo(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    sueldo = models.DecimalField(max_digits=10, decimal_places=2)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='cargos')
    
    class Meta:
        unique_together = ('nombre', 'tenant')
    
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
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='empleados')

    nombre   = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    ci       = models.CharField(max_length=30, verbose_name="CI")
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
        unique_together = ('ci', 'tenant')

    def __str__(self):
        return f"{self.apellido}, {self.nombre} ({self.ci})"

class Bitacora(models.Model):
    class Accion(models.TextChoices):
        CREAR = "CREAR", "Crear"
        EDITAR = "EDITAR", "Editar"
        ELIMINAR = "ELIMINAR", "Eliminar"
        LOGIN = "LOGIN", "Iniciar Sesión"
        LOGOUT = "LOGOUT", "Cerrar Sesión"
        CONSULTAR = "CONSULTAR", "Consultar"
    
    class Modulo(models.TextChoices):
        CARGO = "Cargo", "Cargo"
        CLIENTE = "Cliente", "Cliente"
        EMPLEADO = "Empleado", "Empleado"
        VEHICULO = "Vehiculo", "Vehículo"
        ITEM = "Item", "Item"
        ORDEN_TRABAJO = "OrdenTrabajo", "Orden de Trabajo"
        PRESUPUESTO = "Presupuesto", "Presupuesto"
        AUTENTICACION = "Autenticacion", "Autenticación"
        RECONOCIMIENTO_PLACAS = "ReconocimientoPlacas", "Reconocimiento de Placas"
        CITA = "Cita", "Cita"
        REPORTE = "Reporte", "Reporte"
        ASISTENCIA = "Asistencia", "Asistencia"
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bitacoras')
    accion = models.CharField(max_length=20, choices=Accion.choices)
    modulo = models.CharField(max_length=20, choices=Modulo.choices)
    descripcion = models.TextField()
    ip_address = models.GenericIPAddressField(verbose_name="Dirección IP", null=True, blank=True)
    fecha_accion = models.DateTimeField(auto_now_add=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='bitacoras')
    
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

class Asistencia(models.Model):
    class Estado(models.TextChoices):
        COMPLETO = "completo", "Completo"
        INCOMPLETO = "incompleto", "Incompleto"
        EXTRA = "extra", "Extra"
    
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='asistencias')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='asistencias')
    fecha = models.DateField()
    hora_entrada = models.TimeField()
    hora_salida = models.TimeField(null=True, blank=True)
    horas_extras = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    horas_faltantes = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.INCOMPLETO)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "asistencia"
        unique_together = ('empleado', 'fecha', 'tenant')
        indexes = [
            models.Index(fields=["empleado"]),
            models.Index(fields=["fecha"]),
            models.Index(fields=["estado"]),
        ]
        ordering = ["-fecha", "empleado"]
    
    def calcular_horas(self):
        """Calcula horas extras o faltantes basado en 10 horas de trabajo desde la hora de entrada"""
        from datetime import datetime, timedelta
        
        if not self.hora_salida:
            self.horas_extras = 0.00
            self.horas_faltantes = 0.00
            self.estado = self.Estado.INCOMPLETO
            return
        
        # Convertir horas a datetime para calcular diferencia
        entrada_dt = datetime.combine(self.fecha, self.hora_entrada)
        salida_dt = datetime.combine(self.fecha, self.hora_salida)
        
        # Si la salida es antes de la entrada, asumir que es del día siguiente
        if salida_dt < entrada_dt:
            salida_dt += timedelta(days=1)
        
        # Calcular diferencia total
        diferencia = salida_dt - entrada_dt
        horas_trabajadas = diferencia.total_seconds() / 3600.0  # Convertir a horas
        
        # Horas requeridas: 10 horas
        horas_requeridas = 10.0
        
        if horas_trabajadas >= horas_requeridas:
            # Tiene horas extras
            self.horas_extras = round(horas_trabajadas - horas_requeridas, 2)
            self.horas_faltantes = 0.00
            if self.horas_extras > 0:
                self.estado = self.Estado.EXTRA
            else:
                self.estado = self.Estado.COMPLETO
        else:
            # Le faltan horas
            self.horas_extras = 0.00
            self.horas_faltantes = round(horas_requeridas - horas_trabajadas, 2)
            self.estado = self.Estado.INCOMPLETO
    
    def save(self, *args, **kwargs):
        # Calcular horas antes de guardar
        if self.hora_salida:
            self.calcular_horas()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.empleado} - {self.fecha} ({self.estado})"
    
