from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, F
from .modelsDetallesFactProv import DetalleFacturaProveedor
from .serializers.serializersDetallesFactProv import DetalleFacturaProveedorSerializer


class DetalleFacturaProveedorViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar los detalles de facturas de proveedor.
    Permite listar, crear, actualizar y eliminar detalles de factura.
    """
    queryset = DetalleFacturaProveedor.objects.all()
    serializer_class = DetalleFacturaProveedorSerializer

    def get_queryset(self):
        """
        Filtrado opcional por factura o item
        """
        queryset = super().get_queryset()
        
        # Filtrar por factura
        factura_id = self.request.query_params.get('factura', None)
        if factura_id:
            queryset = queryset.filter(factura_id=factura_id)
        
        # Filtrar por item
        item_id = self.request.query_params.get('item', None)
        if item_id:
            queryset = queryset.filter(item_id=item_id)
            
        return queryset.select_related('factura', 'item')

    @action(detail=False, methods=['get'])
    def por_factura(self, request):
        """
        Listar todos los detalles de una factura específica
        Parámetro requerido: factura_id
        """
        factura_id = request.query_params.get('factura_id')
        
        if not factura_id:
            return Response(
                {"error": "Se requiere el parámetro factura_id"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        detalles = self.queryset.filter(factura_id=factura_id)
        serializer = self.get_serializer(detalles, many=True)
        
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def resumen_factura(self, request):
        """
        Obtener resumen de totales de una factura
        Parámetro requerido: factura_id
        """
        factura_id = request.query_params.get('factura_id')
        
        if not factura_id:
            return Response(
                {"error": "Se requiere el parámetro factura_id"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        detalles = self.queryset.filter(factura_id=factura_id)
        
        # Calcular totales
        resumen = detalles.aggregate(
            total_items=Sum('cantidad'),
            total_subtotal=Sum('subtotal'),
            total_descuento=Sum('descuento'),
            total_final=Sum('total')
        )
        
        resumen['cantidad_detalles'] = detalles.count()
        
        return Response(resumen)

    @action(detail=False, methods=['post'])
    def crear_multiple(self, request):
        """
        Crear múltiples detalles de factura a la vez
        Body esperado: lista de objetos con los datos de cada detalle
        """
        if not isinstance(request.data, list):
            return Response(
                {"error": "Se espera una lista de detalles"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data, many=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """
        Eliminar un detalle de factura
        """
        detalle = self.get_object()
        
        return super().destroy(request, *args, **kwargs)
