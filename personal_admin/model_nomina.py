from django.db import models
from django.core.exceptions import ValidationError
from .models import Empleado
from .models_saas import Tenant


class Nomina(models.Model):
    """
    Modelo para la gestión de nóminas mensuales.
    Almacena información general de la nómina y calcula totales automáticamente.
    """
    class Estado(models.TextChoices):
        PENDIENTE = "Pendiente", "Pendiente"
        PAGADA = "Pagada", "Pagada"
        CANCELADA = "Cancelada", "Cancelada"
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='nominas')
    mes = models.IntegerField(verbose_name="Mes")  # 1-12
    fecha_inicio = models.DateField(verbose_name="Fecha de Inicio")
    fecha_corte = models.DateField(verbose_name="Fecha de Corte")
    fecha_registro = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=20, 
        choices=Estado.choices, 
        default=Estado.PENDIENTE
    )
    total_nomina = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00,
        verbose_name="Total de la Nómina"
    )
    
    class Meta:
        db_table = "nomina"
        unique_together = ('tenant', 'mes', 'fecha_inicio', 'fecha_corte')
        indexes = [
            models.Index(fields=['tenant', 'mes']),
            models.Index(fields=['fecha_inicio']),
            models.Index(fields=['estado']),
        ]
        ordering = ['-fecha_inicio', '-mes']
    
    def clean(self):
        """Validaciones del modelo"""
        if self.mes < 1 or self.mes > 12:
            raise ValidationError({'mes': 'El mes debe estar entre 1 y 12.'})
        
        if self.fecha_corte < self.fecha_inicio:
            raise ValidationError({
                'fecha_corte': 'La fecha de corte debe ser posterior a la fecha de inicio.'
            })
    
    def calcular_total_nomina(self):
        """
        Calcula el total de la nómina sumando todos los sueldos netos
        de los detalles asociados.
        """
        total = self.detalles.aggregate(
            total=models.Sum('sueldo_neto')
        )['total'] or 0.00
        self.total_nomina = total
        return total
    
    def get_periodo(self):
        """
        Retorna el periodo formateado de la nómina.
        """
        meses = [
            "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        mes_nombre = meses[self.mes] if 1 <= self.mes <= 12 else str(self.mes)
        año = self.fecha_inicio.year
        return f"{mes_nombre} {año}"
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        # Actualizar el total después de guardar
        self.calcular_total_nomina()
        if kwargs.get('update_fields') is None:
            # Evitar recursión infinita
            super().save(update_fields=['total_nomina'])
    
    def __str__(self):
        return f"Nómina {self.mes}/{self.fecha_inicio.year} - {self.estado}"


class DetalleNomina(models.Model):
    """
    Modelo para los detalles de nómina por empleado.
    Calcula automáticamente el sueldo bruto, descuentos y sueldo neto
    basándose en la asistencia y el sueldo base del empleado.
    """
    nomina = models.ForeignKey(
        Nomina, 
        on_delete=models.CASCADE, 
        related_name='detalles'
    )
    empleado = models.ForeignKey(
        Empleado, 
        on_delete=models.CASCADE, 
        related_name='detalles_nomina'
    )
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='detalles_nomina')
    
    # Campos calculados
    sueldo = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Sueldo Base"
    )
    horas_extras = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        default=0.00,
        verbose_name="Horas Extras"
    )
    total_bruto = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0.00,
        verbose_name="Total Bruto"
    )
    total_descuento = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0.00,
        verbose_name="Total Descuentos"
    )
    sueldo_neto = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0.00,
        verbose_name="Sueldo Neto"
    )
    
    class Meta:
        db_table = "detalle_nomina"
        unique_together = ('nomina', 'empleado')
        indexes = [
            models.Index(fields=['nomina']),
            models.Index(fields=['empleado']),
        ]
        ordering = ['empleado__apellido', 'empleado__nombre']
    
    def calcular_sueldo_bruto(self):
        """
        Calcula el sueldo bruto considerando:
        - Sueldo base del empleado
        - Horas extras del período de la nómina
        """
        from decimal import Decimal
        from .models import Asistencia
        
        # Obtener el sueldo base del empleado (desde cargo o campo directo)
        if hasattr(self.empleado, 'cargo') and self.empleado.cargo:
            sueldo_base = self.empleado.cargo.sueldo
        else:
            sueldo_base = self.empleado.sueldo
        
        self.sueldo = sueldo_base
        
        # Calcular horas extras del período
        asistencias = Asistencia.objects.filter(
            empleado=self.empleado,
            fecha__gte=self.nomina.fecha_inicio,
            fecha__lte=self.nomina.fecha_corte,
            tenant=self.tenant
        )
        
        total_horas_extras = asistencias.aggregate(
            total=models.Sum('horas_extras')
        )['total'] or Decimal('0.00')
        
        self.horas_extras = total_horas_extras
        
        # Calcular valor de hora extra (ejemplo: 1.5x el valor de hora normal)
        # Asumiendo jornada de 10 horas/día y 26 días/mes = 260 horas/mes
        horas_mes = Decimal('260.00')
        valor_hora_normal = sueldo_base / horas_mes if horas_mes > 0 else Decimal('0.00')
        valor_hora_extra = valor_hora_normal * Decimal('1.5')
        
        monto_horas_extras = self.horas_extras * valor_hora_extra
        
        self.total_bruto = sueldo_base + monto_horas_extras
        
        return self.total_bruto
    
    def calcular_descuentos(self):
        """
        Calcula los descuentos considerando:
        - Horas faltantes del período de la nómina
        - Otros descuentos aplicables
        """
        from decimal import Decimal
        from .models import Asistencia
        
        # Calcular horas faltantes del período
        asistencias = Asistencia.objects.filter(
            empleado=self.empleado,
            fecha__gte=self.nomina.fecha_inicio,
            fecha__lte=self.nomina.fecha_corte,
            tenant=self.tenant
        )
        
        total_horas_faltantes = asistencias.aggregate(
            total=models.Sum('horas_faltantes')
        )['total'] or Decimal('0.00')
        
        # Calcular descuento por horas faltantes
        horas_mes = Decimal('260.00')
        valor_hora_normal = self.sueldo / horas_mes if horas_mes > 0 else Decimal('0.00')
        
        descuento_horas_faltantes = total_horas_faltantes * valor_hora_normal
        
        self.total_descuento = descuento_horas_faltantes
        
        return self.total_descuento
    
    def calcular_sueldo_neto(self):
        """
        Calcula el sueldo neto:
        sueldo_neto = total_bruto - total_descuento
        """
        self.sueldo_neto = self.total_bruto - self.total_descuento
        return self.sueldo_neto
    
    def calcular_todos_los_campos(self):
        """
        Método auxiliar para calcular todos los campos de una vez.
        """
        self.calcular_sueldo_bruto()
        self.calcular_descuentos()
        self.calcular_sueldo_neto()
    
    def save(self, *args, **kwargs):
        """
        Sobrescribe save para calcular automáticamente los campos
        antes de guardar.
        """
        # Calcular todos los campos
        self.calcular_todos_los_campos()
        
        super().save(*args, **kwargs)
        
        # Actualizar el total de la nómina padre
        self.nomina.calcular_total_nomina()
        self.nomina.save(update_fields=['total_nomina'])
    
    def __str__(self):
        return f"{self.empleado} - Nómina {self.nomina.mes}/{self.nomina.fecha_inicio.year}"
