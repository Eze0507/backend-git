from rest_framework import viewsets
from operaciones_inventario.modelsArea import Area
from operaciones_inventario.serializers.serializersArea import AreaSerializer

class AreaViewSet(viewsets.ModelViewSet):
    queryset = Area.objects.all()
    serializer_class = AreaSerializer
