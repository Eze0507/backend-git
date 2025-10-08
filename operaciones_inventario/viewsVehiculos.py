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
        
        # Filtro por número de placa (búsqueda parcial)
        placa = self.request.query_params.get('placa', None)
        if placa:
            queryset = queryset.filter(numero_placa__icontains=placa)
        
        # Filtro por color
        color = self.request.query_params.get('color', None)
        if color:
            queryset = queryset.filter(color__icontains=color)
        
        # Filtro por año
        año = self.request.query_params.get('año', None)
        if año:
            try:
                año_int = int(año)
                queryset = queryset.filter(año=año_int)
            except ValueError:
                pass
        
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
    
    def list(self, request, *args, **kwargs):
        """
        Lista todos los vehículos con los datos más importantes.
        Incluye filtros opcionales por query parameters.
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'count': queryset.count(),
            'results': serializer.data
        })
    
    def create(self, request, *args, **kwargs):
        """
        Crea un nuevo vehículo.
        Valida que el número de placa sea único y que el año esté en el rango válido.
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            vehiculo = serializer.save()
            # Retornar los detalles completos del vehículo creado
            detail_serializer = VehiculoDetailSerializer(vehiculo)
            return Response(detail_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request, *args, **kwargs):
        """
        Retorna los detalles completos de un vehículo específico.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        """
        Actualiza completamente un vehículo existente.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if serializer.is_valid():
            vehiculo = serializer.save()
            # Retornar los detalles completos del vehículo actualizado
            detail_serializer = VehiculoDetailSerializer(vehiculo)
            return Response(detail_serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        """
        Elimina un vehículo.
        El borrado es en cascada si hay dependencias.
        """
        instance = self.get_object()
        marca_nombre = instance.marca.nombre if instance.marca else "Sin marca"
        modelo_nombre = instance.modelo.nombre if instance.modelo else "Sin modelo"
        vehiculo_info = f"{marca_nombre} {modelo_nombre} - {instance.numero_placa}"
        
        instance.delete()
        
        return Response({
            'message': f'Vehículo {vehiculo_info} eliminado correctamente.'
        }, status=status.HTTP_204_NO_CONTENT)
    
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
        """
        modelos = Modelo.objects.all().order_by('nombre')
        serializer = ModeloSerializer(modelos, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        Endpoint para obtener estadísticas básicas de los vehículos.
        """
        total_vehiculos = Vehiculo.objects.count()
        vehiculos_por_marca = {}
        vehiculos_por_año = {}
        
        # Estadísticas por marca
        for vehiculo in Vehiculo.objects.select_related('marca').all():
            marca_nombre = vehiculo.marca.nombre if vehiculo.marca else "Sin marca"
            vehiculos_por_marca[marca_nombre] = vehiculos_por_marca.get(marca_nombre, 0) + 1
        
        # Estadísticas por año
        for vehiculo in Vehiculo.objects.exclude(año__isnull=True):
            año = vehiculo.año
            vehiculos_por_año[año] = vehiculos_por_año.get(año, 0) + 1
        
        return Response({
            'total_vehiculos': total_vehiculos,
            'vehiculos_por_marca': vehiculos_por_marca,
            'vehiculos_por_año': vehiculos_por_año
        })
