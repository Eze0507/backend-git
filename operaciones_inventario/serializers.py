from rest_framework import serializers
from .models import Inventario


class InventarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventario
        fields = ['id', 'categoria', 'codigo', 'descripcion', 'fabricante', 'imagen', 'nombre', 'precio', 'stock', 'tipo']
