from rest_framework import serializers
from decimal import Decimal
from operaciones_inventario.modelsPresupuesto import presupuesto, detallePresupuesto
from operaciones_inventario.modelsVehiculos import Vehiculo
from operaciones_inventario.modelsItem import Item
from clientes_servicios.models import Cliente


class ItemSerializer(serializers.ModelSerializer):
	class Meta:
		model = Item
		fields = ['id', 'codigo', 'nombre', 'descripcion', 'tipo', 'precio']


class DetallePresupuestoSerializer(serializers.ModelSerializer):
	descuento = serializers.SerializerMethodField()
	item = ItemSerializer(read_only=True)
	item_id = serializers.PrimaryKeyRelatedField(
		queryset=Item.objects.all(),
		source='item',
		write_only=True
	)
	
	class Meta:
		model = detallePresupuesto
		fields = ['id', 'presupuesto', 'item', 'item_id', 'cantidad', 'precio_unitario', 'descuento_porcentaje', 'descuento', 'subtotal', 'total']
		read_only_fields = ['descuento', 'subtotal', 'total', 'presupuesto']  # presupuesto es read-only cuando se crea desde el padre

	def get_descuento(self, obj):
		"""Devuelve el descuento calculado como propiedad"""
		return obj.descuento

	def create(self, validated_data):
		detalle = detallePresupuesto(**validated_data)
		detalle.save()
		return detalle

	def update(self, instance, validated_data):
		for attr, value in validated_data.items():
			setattr(instance, attr, value)
		instance.save()
		return instance


class PresupuestoSerializer(serializers.ModelSerializer):
	detalles = DetallePresupuestoSerializer(many=True, required=False)
	vehiculo_id = serializers.PrimaryKeyRelatedField(
		queryset=Vehiculo.objects.all(),
		source='vehiculo',
		write_only=True,
		required=False,
		allow_null=True
	)
	vehiculo = serializers.SerializerMethodField(read_only=True)
	cliente = serializers.PrimaryKeyRelatedField(queryset=Cliente.objects.all(), required=False, allow_null=True)
	cliente_nombre = serializers.SerializerMethodField()
	monto_impuesto = serializers.SerializerMethodField()

	class Meta:
		model = presupuesto
		fields = ['id', 'diagnostico', 'fecha_inicio', 'fecha_fin', 'cliente', 'cliente_nombre', 'estado', 'con_impuestos', 'impuestos', 'monto_impuesto', 'total_descuentos', 'subtotal', 'total', 'vehiculo', 'vehiculo_id', 'detalles']
		read_only_fields = ['monto_impuesto', 'subtotal', 'total', 'total_descuentos', 'cliente_nombre']

	def get_vehiculo(self, obj):
		"""Devuelve el objeto vehículo completo"""
		if obj.vehiculo:
			return {
				'id': obj.vehiculo.id,
				'placa': obj.vehiculo.numero_placa if hasattr(obj.vehiculo, 'numero_placa') else None,
				'marca': obj.vehiculo.marca.nombre if obj.vehiculo.marca else None,
				'modelo': obj.vehiculo.modelo.nombre if obj.vehiculo.modelo else None,
				'año': obj.vehiculo.año if hasattr(obj.vehiculo, 'año') else None,
				'color': obj.vehiculo.color if hasattr(obj.vehiculo, 'color') else None,
			}
		return None

	def get_cliente_nombre(self, obj):
		"""Devuelve el nombre completo del cliente"""
		if obj.cliente:
			return f"{obj.cliente.nombre} {obj.cliente.apellido}".strip()
		return None

	def get_monto_impuesto(self, obj):
		"""Calcula el monto de impuesto basado en el porcentaje y total (CON descuentos) - solo si con_impuestos está activado"""
		if obj.con_impuestos and obj.impuestos and obj.impuestos > 0:
			total_detalles = sum((d.total or Decimal('0.00')) for d in obj.detalles.all())
			
			if obj.impuestos <= 1:
				tasa = obj.impuestos  # Ya es decimal
			else:
				tasa = obj.impuestos / 100  # Convertir porcentaje a decimal
			# El impuesto se calcula sobre total_detalles (después de descuentos)
			return (total_detalles * tasa).quantize(Decimal('0.01'))
		return Decimal('0.00')

	def create(self, validated_data):
		detalles_data = validated_data.pop('detalles', [])
		presup = presupuesto.objects.create(**validated_data)
		for det in detalles_data:
			det['presupuesto'] = presup
			detalle = detallePresupuesto(**det)
			detalle.save()
		presup.recalcular_totales()
		return presup

	def update(self, instance, validated_data):
		detalles_data = validated_data.pop('detalles', None)
		# actualizar campos simples del presupuesto
		for attr, value in validated_data.items():
			setattr(instance, attr, value)
		instance.save()

		if detalles_data is not None:
			# upsert: actualizar detalles con id, crear los nuevos, borrar los que no vienen
			existing = {d.id: d for d in instance.detalles.all()}
			incoming_ids = []
			for det in detalles_data:
				det_id = det.get('id', None)
				if det_id and det_id in existing:
					obj = existing[det_id]
					for k, v in det.items():
						if k != 'id':
							setattr(obj, k, v)
					obj.save()
					incoming_ids.append(det_id)
				else:
					det['presupuesto'] = instance
					new_det = detallePresupuesto(**det)
					new_det.save()
					incoming_ids.append(new_det.id)
			# eliminar los que no están en incoming
			for ex_id, ex_obj in existing.items():
				if ex_id not in incoming_ids:
					ex_obj.delete()

		instance.recalcular_totales()
		return instance

