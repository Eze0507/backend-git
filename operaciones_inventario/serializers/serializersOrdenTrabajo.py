from rest_framework import serializers
from ..modelsOrdenTrabajo import (OrdenTrabajo, DetalleOrdenTrabajo, InventarioVehiculo,  
ItemInventarioVehiculo, TareaOrdenTrabajo, ImagenOrdenTrabajo, PruebaRuta, NotaOrdenTrabajo, 
Inspeccion, AsignacionTecnico, DetalleInspeccion)

class DetalleOrdenTrabajoSerializer(serializers.ModelSerializer):
    nombre_item = serializers.ReadOnlyField() 
    item_nombre = serializers.CharField(source='item.nombre', read_only=True)
    
    class Meta:
        model = DetalleOrdenTrabajo
        fields = [
            'id', 'cantidad', 'precio_unitario', 'descuento', 
            'subtotal', 'total', 
            'item',                   
            'item_personalizado',
            'nombre_item', 'item_nombre'
        ]
        read_only_fields = ['subtotal', 'total']
    
    def validate(self, data):
        """Validación que contempla item_personalizado"""
        item = data.get('item')
        item_personalizado = data.get('item_personalizado')
        if not item and not item_personalizado:
            raise serializers.ValidationError("Debe seleccionar un item del catálogo o especificar un item personalizado")
        if item and item_personalizado:
            raise serializers.ValidationError("No puede seleccionar un item del catálogo Y especificar uno personalizado")
        return data

class OrdenTrabajoSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source='cliente.nombre', read_only=True)
    cliente_telefono = serializers.CharField(source='cliente.telefono', read_only=True)
    vehiculo_placa = serializers.CharField(source='vehiculo.placa', read_only=True)
    vehiculo_modelo = serializers.CharField(source='vehiculo.modelo.nombre', read_only=True)
    vehiculo_marca = serializers.CharField(source='vehiculo.marca.nombre', read_only=True)
    detalles = DetalleOrdenTrabajoSerializer(many=True, required=False)
    
    class Meta:
        model = OrdenTrabajo
        fields = [
            'id', 'fallo_requerimiento', 'estado', 'fecha_creacion',
            'fecha_inicio', 'fecha_finalizacion', 'fecha_entrega',
            'kilometraje', 'nivel_combustible', 'observaciones',
            'subtotal', 'impuesto', 'total', 'descuento',
            'vehiculo', 'cliente', 'cliente_nombre', 'cliente_telefono',
            'vehiculo_placa','vehiculo_modelo' ,'vehiculo_marca', 'detalles'
        ]
        read_only_fields = ['subtotal', 'impuesto', 'total', 'descuento']
    
    def update(self, instance, validated_data):
        """Manejar actualización de detalles"""
        detalles_data = validated_data.pop('detalles', [])
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if detalles_data:
            ids_en_request = [d.get('id') for d in detalles_data if d.get('id')]
            instance.detalles.exclude(id__in=ids_en_request).delete()
            for detalle_data in detalles_data:
                detalle_id = detalle_data.get('id')
                if detalle_id:
                    try:
                        detalle = instance.detalles.get(id=detalle_id)
                        for attr, value in detalle_data.items():
                            if attr != 'id':
                                setattr(detalle, attr, value)
                        detalle.save()
                    except DetalleOrdenTrabajo.DoesNotExist:
                        detalle_data.pop('id', None)
                        DetalleOrdenTrabajo.objects.create(orden_trabajo=instance, **detalle_data)
                else:
                    DetalleOrdenTrabajo.objects.create(orden_trabajo=instance, **detalle_data)
        return instance

class OrdenTrabajoCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear órdenes básicas desde el modal"""
    
    class Meta:
        model = OrdenTrabajo
        fields = [
            'fallo_requerimiento', 'estado', 'fecha_inicio', 
            'fecha_finalizacion', 'fecha_entrega', 'kilometraje', 
            'nivel_combustible', 'observaciones', 'vehiculo', 'cliente'
        ]
    
    def create(self, validated_data):
        """Crear orden con totales inicializados en 0"""
        orden = OrdenTrabajo.objects.create(**validated_data)
        orden.recalcular_totales()  # Inicializar totales en 0
        return orden
