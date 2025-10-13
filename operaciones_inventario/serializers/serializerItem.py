from rest_framework import serializers
from operaciones_inventario.modelsItem import Item

class ItemSerializer(serializers.ModelSerializer):
    area_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = [
            'id', 'codigo', 'nombre', 'descripcion', 'tipo', 'fabricante',
            'precio', 'costo', 'stock', 'imagen', 'estado', 'area', 'area_nombre'
        ]
       

    def get_area_nombre(self, obj):
        return obj.area.nombre if obj.area else None
