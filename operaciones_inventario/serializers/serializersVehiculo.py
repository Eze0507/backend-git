from rest_framework import serializers
from operaciones_inventario.modelsVehiculos import Marca, Modelo, Vehiculo
from clientes_servicios.models import Cliente


class MarcaSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Marca"""
    class Meta:
        model = Marca
        fields = ['id', 'nombre']


class ModeloSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Modelo"""
    marca_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = Modelo
        fields = ['id', 'nombre', 'marca', 'marca_nombre']
    
    def get_marca_nombre(self, obj):
        return obj.marca.nombre if obj.marca else None


class ClienteSerializer(serializers.ModelSerializer):
    """Serializer simplificado para Cliente en el contexto de vehículos"""
    class Meta:
        model = Cliente
        fields = ['id', 'nombre', 'apellido', 'nit', 'tipo_cliente']


class VehiculoListSerializer(serializers.ModelSerializer):
    """Serializer para listar vehículos (datos más importantes)"""
    cliente_nombre = serializers.SerializerMethodField()
    marca_nombre = serializers.SerializerMethodField()
    modelo_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = Vehiculo
        fields = [
            'id', 'cliente_nombre', 'marca_nombre', 'modelo_nombre', 
            'numero_placa', 'color', 'año', 'fecha_registro'
        ]
    
    def get_cliente_nombre(self, obj):
        if obj.cliente:
            return f"{obj.cliente.nombre} {obj.cliente.apellido}".strip()
        return "Sin cliente asignado"
    
    def get_marca_nombre(self, obj):
        return obj.marca.nombre if obj.marca else "Sin marca"
    
    def get_modelo_nombre(self, obj):
        return obj.modelo.nombre if obj.modelo else "Sin modelo"


class VehiculoDetailSerializer(serializers.ModelSerializer):
    """Serializer para detalles completos del vehículo"""
    cliente = ClienteSerializer(read_only=True)
    marca = MarcaSerializer(read_only=True)
    modelo = ModeloSerializer(read_only=True)
    cliente_nombre = serializers.SerializerMethodField()
    marca_nombre = serializers.SerializerMethodField()
    modelo_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = Vehiculo
        fields = [
            'id', 'cliente', 'marca', 'modelo',
            'cliente_nombre', 'marca_nombre', 'modelo_nombre',
            'vin', 'numero_motor', 'numero_placa', 'tipo', 
            'version', 'color', 'año', 'cilindrada', 
            'tipo_combustible', 'fecha_registro'
        ]
    
    def get_cliente_nombre(self, obj):
        if obj.cliente:
            return f"{obj.cliente.nombre} {obj.cliente.apellido}".strip()
        return "Sin cliente asignado"
    
    def get_marca_nombre(self, obj):
        return obj.marca.nombre if obj.marca else "Sin marca"
    
    def get_modelo_nombre(self, obj):
        return obj.modelo.nombre if obj.modelo else "Sin modelo"


class VehiculoCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear y actualizar vehículos"""
    
    class Meta:
        model = Vehiculo
        fields = [
            'id', 'cliente', 'marca', 'modelo', 'vin', 'numero_motor', 
            'numero_placa', 'tipo', 'version', 'color', 'año', 
            'cilindrada', 'tipo_combustible'
        ]
        error_messages = {
            'numero_placa': {
                'unique': 'Ya existe un vehículo con este número de placa.',
                'blank': 'El número de placa es obligatorio.',
                'null': 'El número de placa es obligatorio.',
            }
        }
    
    def validate_numero_placa(self, value):
        """Validación personalizada para el número de placa"""
        if not value:
            raise serializers.ValidationError("El número de placa es obligatorio.")
        
        # Verificar si ya existe otro vehículo con la misma placa
        if self.instance:
            # Si estamos actualizando, excluir el vehículo actual
            if Vehiculo.objects.filter(numero_placa=value).exclude(pk=self.instance.pk).exists():
                raise serializers.ValidationError("Ya existe un vehículo con este número de placa.")
        else:
            # Si estamos creando, verificar que no exista
            if Vehiculo.objects.filter(numero_placa=value).exists():
                raise serializers.ValidationError("Ya existe un vehículo con este número de placa.")
        
        return value
    
    def validate_año(self, value):
        """Validación personalizada para el año"""
        if value is not None and (value < 1950 or value > 2100):
            raise serializers.ValidationError("El año debe estar entre 1950 y 2100.")
        return value
