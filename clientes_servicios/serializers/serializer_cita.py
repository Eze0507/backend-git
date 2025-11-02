from rest_framework import serializers
from ..models import Cita, Cliente
from operaciones_inventario.modelsVehiculos import Vehiculo
from personal_admin.models import Empleado


class ClienteCitaSerializer(serializers.ModelSerializer):
    """Serializer simplificado de Cliente para mostrar en Cita"""
    class Meta:
        model = Cliente
        fields = ['id', 'nombre', 'apellido', 'nit', 'telefono', 'email']
    
    email = serializers.SerializerMethodField()
    
    def get_email(self, obj):
        """Obtener email del usuario asociado si existe"""
        if obj.usuario:
            return obj.usuario.email
        return None


class VehiculoCitaSerializer(serializers.ModelSerializer):
    """Serializer simplificado de Vehículo para mostrar en Cita"""
    class Meta:
        model = Vehiculo
        fields = ['id', 'numero_placa', 'tipo', 'marca', 'modelo', 'color']
    
    marca = serializers.SerializerMethodField()
    modelo = serializers.SerializerMethodField()
    
    def get_marca(self, obj):
        """Obtener nombre de la marca"""
        try:
            if obj and hasattr(obj, 'marca') and obj.marca:
                if hasattr(obj.marca, 'nombre'):
                    return obj.marca.nombre
        except Exception:
            pass
        return None
    
    def get_modelo(self, obj):
        """Obtener nombre del modelo"""
        try:
            if obj and hasattr(obj, 'modelo') and obj.modelo:
                if hasattr(obj.modelo, 'nombre'):
                    return obj.modelo.nombre
        except Exception:
            pass
        return None


class EmpleadoCitaSerializer(serializers.ModelSerializer):
    """Serializer simplificado de Empleado para mostrar en Cita"""
    class Meta:
        model = Empleado
        fields = ['id', 'nombre', 'apellido', 'ci', 'telefono']


class CitaSerializer(serializers.ModelSerializer):
    """Serializer completo para Cita con información relacionada"""
    cliente_info = ClienteCitaSerializer(source='cliente', read_only=True)
    vehiculo_info = VehiculoCitaSerializer(source='vehiculo', read_only=True)
    empleado_info = EmpleadoCitaSerializer(source='empleado', read_only=True)
    
    # Campos para escritura (aceptar IDs)
    cliente = serializers.PrimaryKeyRelatedField(queryset=Cliente.objects.filter(activo=True))
    vehiculo = serializers.PrimaryKeyRelatedField(
        queryset=Vehiculo.objects.all(),
        required=False,
        allow_null=True
    )
    empleado = serializers.PrimaryKeyRelatedField(
        queryset=Empleado.objects.filter(estado=True),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Cita
        fields = [
            'id',
            'cliente',
            'cliente_info',
            'vehiculo',
            'vehiculo_info',
            'empleado',
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
    
    def validate(self, data):
        """Validar que fecha_fin sea posterior a fecha_inicio, que no sean fechas pasadas, y que no choquen con otras citas del mismo empleado"""
        from django.utils import timezone
        from django.db.models import Q
        from ..models import Cita
        
        fecha_inicio = data.get('fecha_hora_inicio')
        fecha_fin = data.get('fecha_hora_fin')
        empleado = data.get('empleado')
        
        # Si estamos actualizando, usar valores existentes si no se proporcionan
        if self.instance:
            fecha_inicio = fecha_inicio or self.instance.fecha_hora_inicio
            fecha_fin = fecha_fin or self.instance.fecha_hora_fin
            empleado = empleado if empleado is not None else self.instance.empleado
        
        ahora = timezone.now()
        
        # Validar que la fecha de inicio no sea en el pasado (solo para nuevas citas)
        if not self.instance and fecha_inicio:
            if fecha_inicio < ahora:
                raise serializers.ValidationError({
                    'fecha_hora_inicio': 'No se pueden agendar citas en el pasado.'
                })
        
        # Validar que la fecha de fin no sea en el pasado (solo para nuevas citas)
        if not self.instance and fecha_fin:
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
            
            # Validar que no choque con otras citas del mismo empleado (si tiene empleado asignado)
            if empleado:
                citas_conflicto = Cita.objects.filter(
                    empleado=empleado,
                    estado__in=['pendiente', 'confirmada'],  # Solo revisar citas activas
                )
                
                # Excluir la cita actual si se está editando
                if self.instance:
                    citas_conflicto = citas_conflicto.exclude(pk=self.instance.pk)
                
                # Verificar solapamiento real: la nueva cita se solapa con una existente si:
                # - La nueva cita comienza antes de que termine la existente
                # - Y la nueva cita termina después de que comience la existente
                citas_conflicto = citas_conflicto.filter(
                    Q(fecha_hora_inicio__lt=fecha_fin, fecha_hora_fin__gt=fecha_inicio)
                )
                
                if citas_conflicto.exists():
                    cita_conflicto = citas_conflicto.first()
                    nombre_empleado = f"{cita_conflicto.empleado.nombre} {cita_conflicto.empleado.apellido}" if cita_conflicto.empleado else "el empleado"
                    raise serializers.ValidationError({
                        'fecha_hora_inicio': f'⚠️ Este horario ya está ocupado. {nombre_empleado} tiene una cita en este horario. Elige otro horario.'
                    })
        
        return data
    
    def validate_vehiculo(self, value):
        """Validar que el vehículo pertenezca al cliente si se proporciona"""
        if value and 'cliente' in self.initial_data:
            cliente_id = self.initial_data.get('cliente')
            if isinstance(cliente_id, Cliente):
                cliente = cliente_id
            else:
                try:
                    cliente = Cliente.objects.get(pk=cliente_id)
                except Cliente.DoesNotExist:
                    raise serializers.ValidationError("Cliente no encontrado.")
            
            if value.cliente != cliente:
                raise serializers.ValidationError("El vehículo seleccionado no pertenece al cliente especificado.")
        
        return value


class CitaCreateSerializer(serializers.ModelSerializer):
    """Serializer simplificado para crear Citas (solo campos requeridos)"""
    cliente = serializers.PrimaryKeyRelatedField(queryset=Cliente.objects.filter(activo=True))
    vehiculo = serializers.PrimaryKeyRelatedField(
        queryset=Vehiculo.objects.all(),
        required=False,
        allow_null=True
    )
    empleado = serializers.PrimaryKeyRelatedField(
        queryset=Empleado.objects.filter(estado=True),
        required=False,
        allow_null=True
    )
    
    def to_internal_value(self, data):
        """Permitir que el campo empleado no esté presente en el request"""
        import copy
        data_copy = copy.deepcopy(data) if isinstance(data, dict) else data
        
        # Si 'empleado' está presente pero es None/vacío, eliminarlo
        if isinstance(data_copy, dict) and 'empleado' in data_copy:
            empleado_value = data_copy['empleado']
            print(f"🔍 Serializer - Campo empleado recibido: {empleado_value} (tipo: {type(empleado_value)})")
            
            if empleado_value in [None, '', 'null', 'undefined']:
                print(f"⚠️ Serializer - Eliminando campo empleado (valor vacío)")
                data_copy.pop('empleado', None)
            else:
                print(f"✅ Serializer - Procesando empleado: {empleado_value}")
        
        return super().to_internal_value(data_copy)
    
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
    
    def validate(self, data):
        """Validar que fecha_fin sea posterior a fecha_inicio, que no sean fechas pasadas, y que no choquen con otras citas del mismo empleado"""
        from django.utils import timezone
        from django.db.models import Q
        from ..models import Cita
        
        fecha_inicio = data.get('fecha_hora_inicio')
        fecha_fin = data.get('fecha_hora_fin')
        empleado = data.get('empleado')
        
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
                citas_conflicto = Cita.objects.filter(
                    empleado=empleado,
                    estado__in=['pendiente', 'confirmada'],  # Solo revisar citas activas
                )
                
                # Excluir la cita actual si se está editando
                if self.instance:
                    citas_conflicto = citas_conflicto.exclude(pk=self.instance.pk)
                
                # Verificar solapamiento real: la nueva cita se solapa con una existente si:
                # - La nueva cita comienza antes de que termine la existente
                # - Y la nueva cita termina después de que comience la existente
                citas_conflicto = citas_conflicto.filter(
                    Q(fecha_hora_inicio__lt=fecha_fin, fecha_hora_fin__gt=fecha_inicio)
                )
                
                if citas_conflicto.exists():
                    cita_conflicto = citas_conflicto.first()
                    nombre_empleado = f"{cita_conflicto.empleado.nombre} {cita_conflicto.empleado.apellido}" if cita_conflicto.empleado else "el empleado"
                    raise serializers.ValidationError({
                        'fecha_hora_inicio': f'⚠️ Este horario ya está ocupado. {nombre_empleado} tiene una cita en este horario. Elige otro horario.'
                    })
        
        # Validar que el vehículo pertenezca al cliente si se proporciona
        vehiculo = data.get('vehiculo')
        cliente = data.get('cliente')
        
        if vehiculo and cliente:
            if vehiculo.cliente != cliente:
                raise serializers.ValidationError({
                    'vehiculo': 'El vehículo seleccionado no pertenece al cliente especificado.'
                })
        
        return data

