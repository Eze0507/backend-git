from rest_framework import serializers
from operaciones_inventario.modelsPresupuesto import presupuesto, detallePresupuesto
from operaciones_inventario.modelsVehiculos import Vehiculo


class DetallePresupuestoSerializer(serializers.ModelSerializer):
	class Meta:
		model = detallePresupuesto
		fields = ['id', 'presupuesto', 'item', 'cantidad', 'precio_unitario', 'descuento', 'subtotal', 'total']
		read_only_fields = ['subtotal', 'total']

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
	vehiculo = serializers.PrimaryKeyRelatedField(queryset=Vehiculo.objects.all(), required=False, allow_null=True)

	class Meta:
		model = presupuesto
		fields = ['id', 'diagnostico', 'fecha_inicio', 'fecha_fin', 'descuento', 'impuestos', 'subtotal', 'total', 'vehiculo', 'detalles']
		read_only_fields = ['subtotal', 'total']

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

