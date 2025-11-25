from rest_framework import serializers
from personal_admin.model_nomina import Nomina, DetalleNomina
from personal_admin.models import Empleado
from personal_admin.serializers.serializers_empleado import EmpleadoReadSerializer


class DetalleNominaMiniSerializer(serializers.ModelSerializer):
    """Serializer básico para detalle de nómina sin empleado anidado"""
    class Meta:
        model = DetalleNomina
        fields = (
            "id", "empleado", "sueldo", "horas_extras", 
            "total_bruto", "total_descuento", "sueldo_neto"
        )


class DetalleNominaReadSerializer(serializers.ModelSerializer):
    """Serializer para lectura de detalle de nómina con información del empleado"""
    empleado = EmpleadoReadSerializer(read_only=True)
    empleado_nombre_completo = serializers.SerializerMethodField()
    
    class Meta:
        model = DetalleNomina
        fields = (
            "id", "nomina", "empleado", "empleado_nombre_completo",
            "sueldo", "horas_extras", "total_bruto", 
            "total_descuento", "sueldo_neto"
        )
        read_only_fields = (
            "horas_extras", "total_bruto", "total_descuento", "sueldo_neto"
        )
    
    def get_empleado_nombre_completo(self, obj):
        """Retorna el nombre completo del empleado"""
        return f"{obj.empleado.nombre} {obj.empleado.apellido}"


class DetalleNominaWriteSerializer(serializers.ModelSerializer):
    """Serializer para escritura de detalle de nómina"""
    empleado_id = serializers.PrimaryKeyRelatedField(
        queryset=Empleado.objects.all(),
        source="empleado",
        write_only=True
    )
    
    class Meta:
        model = DetalleNomina
        fields = (
            "nomina", "empleado_id", "sueldo"
        )
    
    def validate(self, attrs):
        """Validaciones personalizadas"""
        nomina = attrs.get("nomina")
        empleado = attrs.get("empleado")
        
        # Validar que no exista ya un detalle para este empleado en esta nómina
        if self.instance is None:  # Solo en creación
            if DetalleNomina.objects.filter(nomina=nomina, empleado=empleado).exists():
                raise serializers.ValidationError({
                    "empleado_id": f"Ya existe un detalle de nómina para {empleado.nombre} {empleado.apellido} en esta nómina."
                })
        
        # Validar que el sueldo sea positivo
        sueldo = attrs.get("sueldo")
        if sueldo is not None and sueldo < 0:
            raise serializers.ValidationError({
                "sueldo": "El sueldo no puede ser negativo."
            })
        
        return attrs


class NominaReadSerializer(serializers.ModelSerializer):
    """Serializer para lectura de nómina con detalles anidados"""
    detalles = DetalleNominaReadSerializer(many=True, read_only=True)
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    cantidad_empleados = serializers.SerializerMethodField()
    periodo = serializers.SerializerMethodField()
    
    class Meta:
        model = Nomina
        fields = (
            "id", "mes", "fecha_inicio", "fecha_corte", "fecha_registro",
            "estado", "estado_display", "total_nomina", "detalles",
            "cantidad_empleados", "periodo"
        )
        read_only_fields = ("fecha_registro", "total_nomina")
    
    def get_cantidad_empleados(self, obj):
        """Retorna la cantidad de empleados en la nómina"""
        return obj.detalles.count()
    
    def get_periodo(self, obj):
        """Retorna el periodo formateado"""
        meses = [
            "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        mes_nombre = meses[obj.mes] if 1 <= obj.mes <= 12 else str(obj.mes)
        año = obj.fecha_inicio.year
        return f"{mes_nombre} {año}"


class NominaListSerializer(serializers.ModelSerializer):
    """Serializer para listado de nóminas sin detalles anidados"""
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    cantidad_empleados = serializers.SerializerMethodField()
    periodo = serializers.SerializerMethodField()
    
    class Meta:
        model = Nomina
        fields = (
            "id", "mes", "fecha_inicio", "fecha_corte", "fecha_registro",
            "estado", "estado_display", "total_nomina", 
            "cantidad_empleados", "periodo"
        )
        read_only_fields = ("fecha_registro", "total_nomina")
    
    def get_cantidad_empleados(self, obj):
        """Retorna la cantidad de empleados en la nómina"""
        return obj.detalles.count()
    
    def get_periodo(self, obj):
        """Retorna el periodo formateado"""
        meses = [
            "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        mes_nombre = meses[obj.mes] if 1 <= obj.mes <= 12 else str(obj.mes)
        año = obj.fecha_inicio.year
        return f"{mes_nombre} {año}"


class NominaWriteSerializer(serializers.ModelSerializer):
    """Serializer para escritura de nómina"""
    generar_detalles = serializers.BooleanField(
        write_only=True, 
        required=False, 
        default=True,
        help_text="Genera automáticamente detalles para todos los empleados activos"
    )
    
    class Meta:
        model = Nomina
        fields = (
            "mes", "fecha_inicio", "fecha_corte", "estado", "generar_detalles"
        )
    
    def validate(self, attrs):
        """Validaciones personalizadas"""
        mes = attrs.get("mes")
        fecha_inicio = attrs.get("fecha_inicio")
        fecha_corte = attrs.get("fecha_corte")
        tenant = self.context.get('request').user.profile.tenant if self.context.get('request') else None
        
        # Validar mes
        if mes and (mes < 1 or mes > 12):
            raise serializers.ValidationError({
                "mes": "El mes debe estar entre 1 y 12."
            })
        
        # Validar fechas
        if fecha_inicio and fecha_corte and fecha_corte < fecha_inicio:
            raise serializers.ValidationError({
                "fecha_corte": "La fecha de corte debe ser posterior a la fecha de inicio."
            })
        
        # Validar si ya existe una nómina con los mismos datos (solo en creación)
        if self.instance is None and tenant:
            existe = Nomina.objects.filter(
                tenant=tenant,
                mes=mes,
                fecha_inicio=fecha_inicio,
                fecha_corte=fecha_corte
            ).exists()
            
            if existe:
                raise serializers.ValidationError({
                    "mes": "Ya existe una nómina con este mes y fechas para este período."
                })
        
        return attrs
    
    def create(self, validated_data):
        """Crear nómina y generar detalles automáticamente si se solicita"""
        from django.db import transaction
        
        generar_detalles = validated_data.pop("generar_detalles", True)
        tenant = validated_data.get("tenant")
        
        # Usar transacción para asegurar integridad
        with transaction.atomic():
            # Crear la nómina
            nomina = Nomina.objects.create(**validated_data)
            
            # Generar detalles automáticamente para empleados activos
            if generar_detalles:
                empleados_activos = Empleado.objects.filter(
                    estado=True,
                    tenant=tenant
                )
                
                for empleado in empleados_activos:
                    DetalleNomina.objects.create(
                        nomina=nomina,
                        empleado=empleado,
                        tenant=tenant,
                        sueldo=empleado.sueldo
                    )
        
        return nomina
    
    def update(self, instance, validated_data):
        """Actualizar nómina (ignora generar_detalles en edición)"""
        # Remover generar_detalles si existe (no se usa en updates)
        validated_data.pop("generar_detalles", None)
        
        # Actualizar campos
        instance.mes = validated_data.get('mes', instance.mes)
        instance.fecha_inicio = validated_data.get('fecha_inicio', instance.fecha_inicio)
        instance.fecha_corte = validated_data.get('fecha_corte', instance.fecha_corte)
        instance.estado = validated_data.get('estado', instance.estado)
        instance.save()
        
        return instance


class NominaUpdateEstadoSerializer(serializers.ModelSerializer):
    """Serializer para actualizar solo el estado de la nómina"""
    
    class Meta:
        model = Nomina
        fields = ("estado",)
    
    def validate_estado(self, value):
        """Validar transiciones de estado"""
        if self.instance:
            estado_actual = self.instance.estado
            
            # No permitir cambiar de Pagada a Pendiente
            if estado_actual == Nomina.Estado.PAGADA and value == Nomina.Estado.PENDIENTE:
                raise serializers.ValidationError(
                    "No se puede cambiar una nómina pagada a pendiente."
                )
            
            # No permitir modificar nóminas canceladas
            if estado_actual == Nomina.Estado.CANCELADA:
                raise serializers.ValidationError(
                    "No se puede modificar el estado de una nómina cancelada."
                )
        
        return value
