from rest_framework import viewsets
from .modelsInventario import Inventario
from .serializers import InventarioSerializer

class InventarioViewSet(viewsets.ModelViewSet):
    queryset = Inventario.objects.all()
    serializer_class = InventarioSerializer
