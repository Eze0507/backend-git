from rest_framework import serializers
from personal_admin.models import Asistencia, Empleado

class EmpleadoMiniSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.SerializerMethodField()
    
    class Meta:
        model = Empleado
        fields = ("id", "nombre", "apellido", "ci", "nombre_completo")
    
    def get_nombre_completo(self, obj):
        return f"{obj.nombre} {obj.apellido}"

class AsistenciaReadSerializer(serializers.ModelSerializer):
    empleado = EmpleadoMiniSerializer(read_only=True)
    nombre_empleado = serializers.SerializerMethodField()
    horas_trabajadas = serializers.SerializerMethodField()
    horas_extras = serializers.SerializerMethodField()
    horas_faltantes = serializers.SerializerMethodField()
    
    class Meta:
        model = Asistencia
        fields = (
            "id", "empleado", "nombre_empleado", "fecha", "hora_entrada", 
            "hora_salida", "horas_extras", "horas_faltantes", "horas_trabajadas", "estado",
            "fecha_creacion", "fecha_actualizacion"
        )
        read_only_fields = ("horas_extras", "horas_faltantes", "estado", "fecha_creacion", "fecha_actualizacion")
    
    def get_nombre_empleado(self, obj):
        return f"{obj.empleado.nombre} {obj.empleado.apellido}"
    
    def get_horas_trabajadas(self, obj):
        """Calcula las horas trabajadas totales"""
        if not obj.hora_entrada or not obj.hora_salida:
            return None
        
        from datetime import datetime, timedelta
        entrada_dt = datetime.combine(obj.fecha, obj.hora_entrada)
        salida_dt = datetime.combine(obj.fecha, obj.hora_salida)
        
        # Si la salida es antes de la entrada, asumir que es del día siguiente
        if salida_dt < entrada_dt:
            salida_dt += timedelta(days=1)
        
        diferencia = salida_dt - entrada_dt
        horas_trabajadas = diferencia.total_seconds() / 3600.0
        
        return round(horas_trabajadas, 2)
    
    def get_horas_extras(self, obj):
        """Asegura que siempre devuelva un número, 0.00 si no hay extras"""
        return float(obj.horas_extras) if obj.horas_extras else 0.00
    
    def get_horas_faltantes(self, obj):
        """Asegura que siempre devuelva un número, 0.00 si no hay faltantes"""
        return float(obj.horas_faltantes) if obj.horas_faltantes else 0.00

class AsistenciaWriteSerializer(serializers.ModelSerializer):
    empleado_id = serializers.PrimaryKeyRelatedField(
        queryset=Empleado.objects.all(), source="empleado", write_only=True
    )
    
    class Meta:
        model = Asistencia
        fields = ("empleado_id", "fecha", "hora_entrada", "hora_salida")
    
    def validate(self, attrs):
        fecha = attrs.get("fecha")
        empleado = attrs.get("empleado")
        tenant = self.context.get("tenant")
        
        if not tenant:
            raise serializers.ValidationError("Tenant no proporcionado en el contexto")
        
        # Verificar que el empleado pertenezca al tenant
        if empleado.tenant != tenant:
            raise serializers.ValidationError({"empleado_id": "El empleado no pertenece a este tenant"})
        
        # Verificar que no exista ya una asistencia para este empleado en esta fecha
        if self.instance is None:  # Solo al crear
            if Asistencia.objects.filter(empleado=empleado, fecha=fecha, tenant=tenant).exists():
                raise serializers.ValidationError("Ya existe una asistencia para este empleado en esta fecha")
        
        return attrs

class AsistenciaMarcarSerializer(serializers.Serializer):
    """Serializer para que el empleado marque entrada o salida"""
    tipo = serializers.ChoiceField(choices=["entrada", "salida"])
    
    def validate(self, attrs):
        return attrs








