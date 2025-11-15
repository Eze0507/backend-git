from rest_framework import serializers
from operaciones_inventario.modelsArea import Area

class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = ['id', 'nombre']
