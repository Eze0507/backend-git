from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .modelsFactProv import FacturaProveedor
from .serializers.serializersFactProv import FacturaProveedorSerializer
from rest_framework.permissions import IsAuthenticated


class FacturaProveedorViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar las facturas de proveedor.
    Permite listar, crear, actualizar y eliminar facturas.
    """
    serializer_class = FacturaProveedorSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Filtrado opcional por proveedor, número de factura o fecha
        """
        
        user_tenant = self.request.user.profile.tenant
        queryset = FacturaProveedor.objects.filter(
            tenant=user_tenant
        )
        
        # Filtrar por proveedor
        proveedor_id = self.request.query_params.get('proveedor', None)
        if proveedor_id:
            queryset = queryset.filter(proveedor_id=proveedor_id)
        
        # Filtrar por número de factura
        numero = self.request.query_params.get('numero', None)
        if numero:
            queryset = queryset.filter(numero__icontains=numero)
        
        # Filtrar por fecha
        fecha_desde = self.request.query_params.get('fecha_desde', None)
        fecha_hasta = self.request.query_params.get('fecha_hasta', None)
        if fecha_desde:
            queryset = queryset.filter(fecha_registro__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha_registro__lte=fecha_hasta)
            
        return queryset.select_related('proveedor')
    
    def perform_create(self, serializer):
        """Crear factura de proveedor y asignar el TENANT automáticamente"""
        user_tenant = self.request.user.profile.tenant
        instance = serializer.save(tenant=user_tenant)
        # (Aquí iría tu lógica de bitácora para la creación)
        
    def perform_update(self, serializer):
        """Actualizar factura de proveedor y asignar el TENANT automáticamente"""
        # (Añadido por seguridad, aunque get_object() ya protege)
        user_tenant = self.request.user.profile.tenant
        instance = serializer.save(tenant=user_tenant)

    @action(detail=True, methods=['get'])
    def detalles(self, request, pk=None):
        """
        Obtener los detalles de una factura específica
        """
        factura = self.get_object()
        detalles = factura.detalles.all()
        
        from .serializers.serializersDetallesFactProv import DetalleFacturaProveedorSerializer
        serializer = DetalleFacturaProveedorSerializer(detalles, many=True)
        
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def recalcular(self, request, pk=None):
        """
        Recalcular el subtotal, descuento, impuesto y total de una factura
        basándose en los detalles actuales.
        """
        factura = self.get_object()
        
        # Recalcular desde detalles
        factura.recalcular_desde_detalles()
        factura.save()
        
        # Serializar y devolver la factura actualizada
        serializer = self.get_serializer(factura)
        
        return Response({
            'mensaje': 'Factura recalculada correctamente',
            'factura': serializer.data
        })

    @action(detail=False, methods=['get'])
    def por_proveedor(self, request):
        """
        Listar todas las facturas de un proveedor específico
        Parámetro requerido: proveedor_id
        """
        proveedor_id = request.query_params.get('proveedor_id')
        
        if not proveedor_id:
            return Response(
                {"error": "Se requiere el parámetro proveedor_id"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        facturas = self.get_queryset().filter(proveedor_id=proveedor_id)
        serializer = self.get_serializer(facturas, many=True)
        
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def buscar(self, request):
        """
        Búsqueda general por número de factura u observaciones
        Parámetro: q (query de búsqueda)
        """
        query = request.query_params.get('q', None)
        
        if not query:
            return Response(
                {"error": "Se requiere el parámetro q para buscar"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        facturas = self.get_queryset().filter(
            Q(numero__icontains=query) | 
            Q(observacion__icontains=query)
        )
        
        serializer = self.get_serializer(facturas, many=True)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        Eliminar una factura (con confirmación)
        """
        factura = self.get_object()
        
        # Verificar si tiene detalles asociados
        if factura.detalles.exists():
            return Response(
                {
                    "error": "No se puede eliminar la factura porque tiene detalles asociados. Elimine primero los detalles."
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().destroy(request, *args, **kwargs)
