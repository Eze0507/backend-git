from rest_framework import viewsets
from operaciones_inventario.modelsItem import Item
from operaciones_inventario.serializers.serializerItem import ItemSerializer

class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
