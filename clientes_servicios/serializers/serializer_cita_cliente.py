from rest_framework import serializers
from ..models import Cita, Cliente
from operaciones_inventario.modelsVehiculos import Vehiculo
from personal_admin.models import Empleado
from .serializer_cita import (
    ClienteCitaSerializer,
    VehiculoCitaSerializer,
    EmpleadoCitaSerializer
)


class CitaClienteSerializer(serializers.ModelSerializer):
    """Serializer para que clientes vean sus citas"""
    cliente_info = ClienteCitaSerializer(source='cliente', read_only=True)
    vehiculo_info = VehiculoCitaSerializer(source='vehiculo', read_only=True)
    empleado_info = EmpleadoCitaSerializer(source='empleado', read_only=True)
    
    class Meta:
        model = Cita
        fields = [
            'id',
            'cliente_info',
            'vehiculo_info',
            'empleado_info',
            'fecha_hora_inicio',
            'fecha_hora_fin',
            'tipo_cita',
            'estado',
            'descripcion',
            'nota',
            'fecha_creacion',
            'fecha_actualizacion',
        ]
        read_only_fields = ['fecha_creacion', 'fecha_actualizacion']


class CitaClienteCreateSerializer(serializers.ModelSerializer):
    """Serializer para que clientes creen citas"""
    # El cliente se asigna automáticamente desde el usuario autenticado
    cliente = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.filter(activo=True),
        required=False
    )
    vehiculo = serializers.PrimaryKeyRelatedField(
        queryset=Vehiculo.objects.all(),
        required=False,
        allow_null=True
    )
    empleado = serializers.PrimaryKeyRelatedField(
        queryset=Empleado.objects.filter(estado=True),
        required=True  # El cliente DEBE seleccionar un empleado
    )
    
    class Meta:
        model = Cita
        fields = [
            'cliente',
            'vehiculo',
            'empleado',
            'fecha_hora_inicio',
            'fecha_hora_fin',
            'tipo_cita',
            'estado',
            'descripcion',
            'nota',
        ]
        extra_kwargs = {
            'estado': {'required': False, 'default': 'confirmada'}
        }
    
    def validate(self, data):
        """Validar que fecha_fin sea posterior a fecha_inicio, que no sean fechas pasadas, y que no choquen con otras citas del mismo empleado"""
        from django.utils import timezone
        from django.db.models import Q
        from datetime import datetime
        
        fecha_inicio = data.get('fecha_hora_inicio')
        fecha_fin = data.get('fecha_hora_fin')
        empleado = data.get('empleado')
        
        # Asegurar que las fechas estén en timezone aware
        if fecha_inicio and timezone.is_naive(fecha_inicio):
            # Si es naive, asumir que es UTC
            fecha_inicio = timezone.make_aware(fecha_inicio, timezone.utc)
            data['fecha_hora_inicio'] = fecha_inicio
        
        if fecha_fin and timezone.is_naive(fecha_fin):
            fecha_fin = timezone.make_aware(fecha_fin, timezone.utc)
            data['fecha_hora_fin'] = fecha_fin
        
        ahora = timezone.now()
        
        # Validar que la fecha de inicio no sea en el pasado
        if fecha_inicio:
            if fecha_inicio < ahora:
                raise serializers.ValidationError({
                    'fecha_hora_inicio': 'No se pueden agendar citas en el pasado.'
                })
        
        # Validar que la fecha de fin no sea en el pasado
        if fecha_fin:
            if fecha_fin < ahora:
                raise serializers.ValidationError({
                    'fecha_hora_fin': 'No se pueden agendar citas en el pasado.'
                })
        
        # Validar que fecha_fin sea posterior a fecha_inicio
        if fecha_inicio and fecha_fin:
            if fecha_fin <= fecha_inicio:
                raise serializers.ValidationError({
                    'fecha_hora_fin': 'La fecha y hora de fin debe ser posterior a la fecha y hora de inicio.'
                })
            
            # Validar que ambas fechas estén en el mismo día
            if fecha_inicio.date() != fecha_fin.date():
                raise serializers.ValidationError({
                    'fecha_hora_fin': 'La cita debe comenzar y terminar el mismo día. Una cita no puede durar más de un día.'
                })
            
            # Validar que la duración no exceda 2 horas
            duracion = fecha_fin - fecha_inicio
            if duracion.total_seconds() > 2 * 3600:  # 2 horas en segundos
                raise serializers.ValidationError({
                    'fecha_hora_fin': 'La duración máxima de una cita es de 2 horas.'
                })
            
            # Validar que no choque con otras citas del mismo empleado
            if empleado:
                print(f"🔍 [VALIDACIÓN] Validando conflicto para empleado {empleado.id}")
                print(f"🔍 [VALIDACIÓN] Nueva cita: {fecha_inicio} a {fecha_fin}")
                
                citas_conflicto = Cita.objects.filter(
                    empleado=empleado,
                    estado__in=['pendiente', 'confirmada'],  # Solo revisar citas activas
                )
                
                # Debug: mostrar todas las citas del empleado
                todas_citas = list(citas_conflicto.values('id', 'fecha_hora_inicio', 'fecha_hora_fin'))
                print(f"🔍 [VALIDACIÓN] Total citas del empleado: {len(todas_citas)}")
                for c in todas_citas:
                    print(f"  - Cita {c['id']}: {c['fecha_hora_inicio']} a {c['fecha_hora_fin']}")
                
                # Verificar solapamiento real
                citas_conflicto = citas_conflicto.filter(
                    Q(fecha_hora_inicio__lt=fecha_fin, fecha_hora_fin__gt=fecha_inicio)
                )
                
                print(f"🔍 [VALIDACIÓN] Citas con conflicto después del filtro: {citas_conflicto.count()}")
                
                if citas_conflicto.exists():
                    cita_conflicto = citas_conflicto.first()
                    print(f"🔍 [VALIDACIÓN] Conflicto encontrado con cita {cita_conflicto.id}: {cita_conflicto.fecha_hora_inicio} a {cita_conflicto.fecha_hora_fin}")
                    nombre_empleado = f"{cita_conflicto.empleado.nombre} {cita_conflicto.empleado.apellido}" if cita_conflicto.empleado else "el empleado"
                    raise serializers.ValidationError({
                        'fecha_hora_inicio': f'⚠️ Este horario ya está ocupado. {nombre_empleado} tiene una cita en este horario. Elige otro horario.'
                    })
        
        # Validar que el vehículo pertenezca al cliente si se proporciona
        # Nota: El cliente se asigna automáticamente en perform_create, 
        # pero podemos validar el vehículo si se proporciona
        vehiculo = data.get('vehiculo')
        
        # Si hay un vehículo, validaremos que pertenezca al cliente en perform_create
        # Por ahora solo validamos que exista
        if vehiculo:
            # La validación de que pertenece al cliente se hará en perform_create
            pass
        
        return data


class EmpleadoCalendarioSerializer(serializers.Serializer):
    """Serializer para mostrar horarios ocupados de un empleado (sin detalles)"""
    fecha_hora_inicio = serializers.CharField()  # Aceptar string ISO
    fecha_hora_fin = serializers.CharField()  # Aceptar string ISO
    ocupado = serializers.BooleanField(default=True)



