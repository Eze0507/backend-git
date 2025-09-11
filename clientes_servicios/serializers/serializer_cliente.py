# clientes_servicios/serializers/serializer_cliente.py
from rest_framework import serializers
from ..models import Cliente

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = [
            'id', 'nombre', 'apellido', 'nit', 'correo', 'telefono',
            'direccion', 'tipo_cliente', 'activo', 'fecha_registro', 'fecha_actualizacion'
        ]
        read_only_fields = ('id', 'fecha_registro', 'fecha_actualizacion')

    def validate_nit(self, value):
        return value.strip()
