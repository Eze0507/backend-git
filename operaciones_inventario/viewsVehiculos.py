from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .modelsVehiculos import Vehiculo, Marca, Modelo
from .serializers.serializersVehiculo import (
    VehiculoListSerializer, 
    VehiculoDetailSerializer, 
    VehiculoCreateUpdateSerializer,
    MarcaSerializer,
    ModeloSerializer
)


class VehiculoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para el CRUD completo de vehículos.
    
    Endpoints disponibles:
    - GET /api/vehiculos/ - Listar todos los vehículos
    - POST /api/vehiculos/ - Crear un nuevo vehículo
    - GET /api/vehiculos/{id}/ - Ver detalles de un vehículo
    - PUT /api/vehiculos/{id}/ - Actualizar un vehículo completo
    - PATCH /api/vehiculos/{id}/ - Actualizar parcialmente un vehículo
    - DELETE /api/vehiculos/{id}/ - Eliminar un vehículo
    """
    
    queryset = Vehiculo.objects.select_related('cliente', 'marca', 'modelo').all()
    
    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción"""
        if self.action == 'list':
            return VehiculoListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return VehiculoCreateUpdateSerializer
        else:
            return VehiculoDetailSerializer
    
    def get_queryset(self):
        """Filtros opcionales para la consulta"""
        queryset = super().get_queryset()
        
        # Filtro por cliente
        cliente_id = self.request.query_params.get('cliente_id', None)
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        
        # Filtro por marca
        marca_id = self.request.query_params.get('marca_id', None)
        if marca_id:
            queryset = queryset.filter(marca_id=marca_id)
        
        # Filtro por modelo
        modelo_id = self.request.query_params.get('modelo_id', None)
        if modelo_id:
            queryset = queryset.filter(modelo_id=modelo_id)
        
        # Búsqueda general
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(numero_placa__icontains=search) |
                Q(vin__icontains=search) |
                Q(numero_motor__icontains=search) |
                Q(cliente__nombre__icontains=search) |
                Q(cliente__apellido__icontains=search) |
                Q(marca__nombre__icontains=search) |
                Q(modelo__nombre__icontains=search)
            )    
        return queryset.order_by('-fecha_registro')
    @action(detail=False, methods=['get'])
    def marcas(self, request):
        """
        Endpoint para obtener todas las marcas disponibles.
        Útil para autocompletado en el frontend.
        """
        marcas = Marca.objects.all().order_by('nombre')
        serializer = MarcaSerializer(marcas, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def modelos(self, request):
        """
        Endpoint para obtener todos los modelos disponibles.
        Útil para autocompletado en el frontend.
        
        Parámetros opcionales:
        - marca_id: Filtrar modelos por marca específica
        """
        modelos = Modelo.objects.select_related('marca').all()
        
        # Filtro por marca si se proporciona
        marca_id = request.query_params.get('marca_id', None)
        if marca_id:
            modelos = modelos.filter(marca_id=marca_id)
        
        modelos = modelos.order_by('marca__nombre', 'nombre')
        serializer = ModeloSerializer(modelos, many=True)
        return Response(serializer.data)
    
