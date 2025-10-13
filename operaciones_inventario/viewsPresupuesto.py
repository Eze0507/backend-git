from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
from .modelsPresupuesto import presupuesto, detallePresupuesto
from .serializers.serializersPresupuesto import PresupuestoSerializer, DetallePresupuestoSerializer


class DetallePresupuestoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de Detalles de Presupuesto.
    Permite crear, leer, actualizar y eliminar detalles de presupuesto de forma independiente.
    """
    queryset = detallePresupuesto.objects.all()
    serializer_class = DetallePresupuestoSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        presupuesto_id = self.request.query_params.get('presupuesto_id', None)
        if presupuesto_id:
            queryset = queryset.filter(presupuesto_id=presupuesto_id)

        item_id = self.request.query_params.get('item_id', None)
        if item_id:
            queryset = queryset.filter(item_id=item_id)

        return queryset.order_by('id')

    def create(self, request, *args, **kwargs):
        """Crear un nuevo detalle de presupuesto"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            detalle = serializer.save()
            # Recalcular totales del presupuesto padre
            if detalle.presupuesto:
                detalle.presupuesto.recalcular_totales()
            return Response(DetallePresupuestoSerializer(detalle).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        """Actualizar un detalle de presupuesto existente"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            detalle = serializer.save()
            # Recalcular totales del presupuesto padre
            if detalle.presupuesto:
                detalle.presupuesto.recalcular_totales()
            return Response(DetallePresupuestoSerializer(detalle).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """Eliminar un detalle de presupuesto"""
        instance = self.get_object()
        presupuesto_padre = instance.presupuesto
        instance.delete()
        # Recalcular totales del presupuesto padre después de eliminar
        if presupuesto_padre:
            presupuesto_padre.recalcular_totales()
        return Response({'message': 'Detalle de presupuesto eliminado correctamente.'}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Crear múltiples detalles de presupuesto a la vez"""
        detalles_data = request.data if isinstance(request.data, list) else [request.data]
        serializer = DetallePresupuestoSerializer(data=detalles_data, many=True)
        if serializer.is_valid():
            detalles = serializer.save()
            # Recalcular totales para todos los presupuestos afectados
            presupuestos_afectados = set()
            for detalle in detalles:
                if detalle.presupuesto:
                    presupuestos_afectados.add(detalle.presupuesto)
            for presup in presupuestos_afectados:
                presup.recalcular_totales()
            return Response(DetallePresupuestoSerializer(detalles, many=True).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PresupuestoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de Presupuestos.
    """
    queryset = presupuesto.objects.all().prefetch_related('detalles')
    serializer_class = PresupuestoSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        vehiculo_id = self.request.query_params.get('vehiculo_id', None)
        if vehiculo_id:
            queryset = queryset.filter(vehiculo_id=vehiculo_id)

        fecha_inicio = self.request.query_params.get('fecha_inicio', None)
        if fecha_inicio:
            queryset = queryset.filter(fecha_inicio=fecha_inicio)

        return queryset.order_by('-id')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            presup = serializer.save()
            return Response(PresupuestoSerializer(presup).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            presup = serializer.save()
            return Response(PresupuestoSerializer(presup).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({'message': 'Presupuesto eliminado correctamente.'}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def detalles(self, request, pk=None):
        presup = self.get_object()
        detalles = presup.detalles.all()
        serializer = DetallePresupuestoSerializer(detalles, many=True)
        return Response(serializer.data)
