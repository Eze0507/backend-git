from rest_framework import viewsets
from operaciones_inventario.modelsProveedor import Proveedor
from operaciones_inventario.serializers.serializersProveedor import ProveedorSerializer

class ProveedorViewSet(viewsets.ModelViewSet):
    queryset = Proveedor.objects.all();
    serializer_class = ProveedorSerializer