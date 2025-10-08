
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .modelsInventario import Inventario
from .serializerInventario import InventarioSerializer

class InventarioViewSet(viewsets.ModelViewSet):
    queryset = Inventario.objects.all()
    serializer_class = InventarioSerializer

    @action(detail=True, methods=['post'])
    def vender(self, request, pk=None):
        """
        Endpoint para vender una cantidad de un producto y reducir el stock.
        POST /api/inventarios/{id}/vender/ {"cantidad": 2}
        """
        inventario = self.get_object()
        cantidad = int(request.data.get('cantidad', 1))
        if cantidad < 1:
            return Response({'error': 'La cantidad debe ser mayor a 0.'}, status=status.HTTP_400_BAD_REQUEST)
        if inventario.stock < cantidad:
            return Response({'error': 'Stock insuficiente.'}, status=status.HTTP_400_BAD_REQUEST)
        inventario.stock -= cantidad
        inventario.save()
        return Response({'mensaje': f'Stock actualizado. Nuevo stock: {inventario.stock}'}, status=status.HTTP_200_OK)
