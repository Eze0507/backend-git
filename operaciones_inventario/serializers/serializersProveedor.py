from rest_framework import serializers
from operaciones_inventario.modelsProveedor import Proveedor

class ProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proveedor
        fields = '__all__'