from rest_framework import viewsets
from operaciones_inventario.modelsArea import Area
from operaciones_inventario.serializers.serializersArea import AreaSerializer

# NUEVO: Asegúrate de importar IsAuthenticated
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets

# (Aquí irían tus otras importaciones: Area, AreaSerializer)

class AreaViewSet(viewsets.ModelViewSet):
    
    serializer_class = AreaSerializer
    #permission_classes = [IsAuthenticated]
    def get_queryset(self):
        user_tenant = self.request.user.profile.tenant
        return Area.objects.filter(tenant=user_tenant)
    
    def perform_create(self, serializer):
        user_tenant = self.request.user.profile.tenant
        instance = serializer.save(tenant=user_tenant)

