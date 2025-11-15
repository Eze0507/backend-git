from rest_framework import viewsets
from operaciones_inventario.modelsProveedor import Proveedor
from operaciones_inventario.serializers.serializersProveedor import ProveedorSerializer

class ProveedorViewSet(viewsets.ModelViewSet):
    serializer_class = ProveedorSerializer
    
    def get_queryset(self):
        user_tenant = self.request.user.profile.tenant
        return Proveedor.objects.filter(tenant=user_tenant)
    
    def perform_create(self, serializer):
        user_tenant = self.request.user.profile.tenant
        isinstance = serializer.save(tenant=user_tenant)