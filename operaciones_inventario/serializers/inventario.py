from rest_framework import serializers
from operaciones_inventario.modelsInventario import Inventario

class InventarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventario
        fields = '__all__'
