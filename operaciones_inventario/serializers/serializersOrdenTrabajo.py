from rest_framework import serializers

from personal_admin import models
from ..modelsOrdenTrabajo import OrdenTrabajo, InventarioVehiculo
from ..modelsVehiculos import Vehiculo
from clientes_servicios.models import Cliente
from ..modelsOrdenTrabajo import (OrdenTrabajo, DetalleOrdenTrabajo, TareaOrdenTrabajo, ImagenOrdenTrabajo, 
PruebaRuta, NotaOrdenTrabajo, AsignacionTecnico, InventarioVehiculo, Inspeccion, PruebaRuta)

class ImagenOrdenTrabajoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagenOrdenTrabajo
        fields = ['id', 'imagen_url', 'descripcion']

class AsignacionTecnicoSerializer(serializers.ModelSerializer):
    tecnico_nombre = serializers.CharField(source='tecnico.nombre', read_only=True)
    
    class Meta:
        model = AsignacionTecnico
        fields = ['id', 'tecnico', 'tecnico_nombre', 'fecha_asignacion']
        read_only_fields = ['fecha_asignacion']

class PruebaRutaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PruebaRuta
        fields = ['id', 'orden_trabajo', 'fecha_prueba', 'tipo_prueba', 'kilometraje_inicio', 'kilometraje_final', 
                'ruta', 'frenos', 'motor', 'suspension', 'direccion', 'observaciones', 'tecnico']
        read_only_fields = ['fecha_prueba']

class inspeccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inspeccion
        fields = ['id','orden_trabajo', 'tipo_inspeccion', 'fecha', 'tecnico', 'aceite_motor', 'Filtros_VH', 
                'nivel_refrigerante', 'pastillas_freno', 'Estado_neumaticos', 'estado_bateria', 
                'estado_luces', 'observaciones_generales']
        read_only_fields = ['fecha']

class inventarioVehiculoSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventarioVehiculo
        fields = [
            'id', 'orden_trabajo', 'fecha_creacion', 'extintor', 
            'botiquin', 'antena', 'llanta_repuesto', 'documentos', 
            'encendedor', 'pisos', 'luces', 'llaves', 'gata', 
            'herramientas', 'tapas_ruedas', 'triangulos'
        ]
        read_only_fields = ['fecha_creacion']

class TareaOrdenTrabajoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TareaOrdenTrabajo
        fields = ['id', 'descripcion', 'completada']

class NotaOrdenTrabajoSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotaOrdenTrabajo
        fields = ['id', 'contenido', 'fecha_nota']
        read_only_fields = ['fecha_nota']

class DetalleOrdenTrabajoSerializer(serializers.ModelSerializer):
    nombre_item = serializers.ReadOnlyField() 
    item_nombre = serializers.CharField(source='item.nombre', read_only=True)
    
    class Meta:
        model = DetalleOrdenTrabajo
        fields = [
            'id', 'cantidad', 'precio_unitario', 
            'descuento', 'descuento_porcentaje',
            'subtotal', 'total', 
            'item',                   
            'item_personalizado',
            'nombre_item', 'item_nombre'
        ]
        read_only_fields = ['subtotal', 'total']
    
    def validate(self, data):
        from decimal import Decimal
        # Validación item o personalizado
        item = data.get('item', getattr(self.instance, 'item', None))
        item_personalizado = data.get('item_personalizado', getattr(self.instance, 'item_personalizado', None))
        if not item and not item_personalizado:
            raise serializers.ValidationError("Debe seleccionar un item del catálogo o especificar un item personalizado")
        if item and item_personalizado:
            raise serializers.ValidationError("No puede seleccionar un item del catálogo Y especificar uno personalizado")

        # No combinar porcentaje y monto fijo
        d_pct = data.get('descuento_porcentaje', getattr(self.instance, 'descuento_porcentaje', 0) or 0)
        d_monto = data.get('descuento', getattr(self.instance, 'descuento', 0) or 0)
        if Decimal(str(d_pct)) > 0 and Decimal(str(d_monto)) > 0:
            raise serializers.ValidationError("Use descuento PORCENTAJE o descuento MONTO, no ambos a la vez")
        return data

class OrdenTrabajoSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source='cliente.nombre', read_only=True)
    cliente_telefono = serializers.CharField(source='cliente.telefono', read_only=True)
    vehiculo_placa = serializers.CharField(source='vehiculo.placa', read_only=True)
    vehiculo_modelo = serializers.CharField(source='vehiculo.modelo.nombre', read_only=True)
    vehiculo_marca = serializers.CharField(source='vehiculo.marca.nombre', read_only=True)
    detalles = DetalleOrdenTrabajoSerializer(many=True, required=False)
    notas = NotaOrdenTrabajoSerializer(many=True, read_only=True)
    tareas = TareaOrdenTrabajoSerializer(many=True, read_only=True)
    inventario_vehiculo = inventarioVehiculoSerializer(many=True, read_only=True)
    inspecciones = inspeccionSerializer(many=True, read_only=True)
    pruebas_ruta = PruebaRutaSerializer(many=True, read_only=True)
    asignaciones_tecnicos = AsignacionTecnicoSerializer(many=True, read_only=True)
    imagenes = ImagenOrdenTrabajoSerializer(many=True, read_only=True)
    
    class Meta:
        model = OrdenTrabajo
        fields = [
            'id', 'fallo_requerimiento', 'estado', 'fecha_creacion',
            'fecha_inicio', 'fecha_finalizacion', 'fecha_entrega',
            'kilometraje', 'nivel_combustible', 'observaciones',
            'subtotal', 'impuesto', 'total', 'descuento', 'pago',
            'vehiculo', 'cliente', 'cliente_nombre', 'cliente_telefono',
            'vehiculo_placa','vehiculo_modelo' ,'vehiculo_marca', 'detalles',
            'notas', 'tareas', 'inventario_vehiculo', 'inspecciones', 'pruebas_ruta',
            'asignaciones_tecnicos', 'imagenes'
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
    
    def __init__(self, *args, **kwargs):
        """
        Filtra los querysets de 'vehiculo' y 'cliente' 
        para mostrar solo los que pertenecen al tenant del usuario.
        """
        super().__init__(*args, **kwargs)
        
        # Asegurarse de que el contexto (y el request) existan
        if 'request' in self.context:
            user_tenant = self.context['request'].user.profile.tenant
            
            # Filtrar 'vehiculo' y 'cliente' por el tenant
            self.fields['vehiculo'].queryset = Vehiculo.objects.filter(tenant=user_tenant)
            self.fields['cliente'].queryset = Cliente.objects.filter(tenant=user_tenant)
    
    def create(self, validated_data):
        """Crear orden con totales inicializados en 0"""
        user_tenant = self.context['request'].user.profile.tenant
        orden = OrdenTrabajo.objects.create(tenant=user_tenant, **validated_data)
        InventarioVehiculo.objects.create(orden_trabajo=orden, tenant=user_tenant)
        orden.recalcular_totales()  # Inicializar totales en 0
        return orden
