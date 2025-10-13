from rest_framework import viewsets
from rest_framework.response import Response
from .modelsOrdenTrabajo import OrdenTrabajo, DetalleOrdenTrabajo
from .serializers.serializersOrdenTrabajo import OrdenTrabajoSerializer, DetalleOrdenTrabajoSerializer, OrdenTrabajoCreateSerializer


class OrdenTrabajoViewSet(viewsets.ModelViewSet):
    queryset = OrdenTrabajo.objects.all()
    
    def get_serializer_class(self):
        """Usar diferentes serializers según la acción"""
        if self.action == 'create':
            return OrdenTrabajoCreateSerializer  
        return OrdenTrabajoSerializer         
    
    def get_queryset(self):
        """Optimizar consultas con select_related y prefetch_related"""
        return OrdenTrabajo.objects.select_related(
            'cliente', 'vehiculo'
        ).prefetch_related('detalles', 'detalles__item')

class DetalleOrdenTrabajoViewSet(viewsets.ModelViewSet):
    serializer_class = DetalleOrdenTrabajoSerializer
    
    def get_queryset(self):
        """Filtrar por orden si se pasa el parámetro"""
        if 'orden_pk' in self.kwargs:
            return DetalleOrdenTrabajo.objects.filter(
                orden_trabajo_id=self.kwargs['orden_pk']
            ).select_related('item', 'orden_trabajo')
        return DetalleOrdenTrabajo.objects.all()
    
    def perform_create(self, serializer):
        """Asignar la orden automáticamente al crear detalle"""
        if 'orden_pk' in self.kwargs:
            orden = OrdenTrabajo.objects.get(pk=self.kwargs['orden_pk'])
            serializer.save(orden_trabajo=orden)
        else:
            serializer.save()