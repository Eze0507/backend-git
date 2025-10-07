from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from .modelsServicios import Area, Categoria, Servicio
from .serializers.serializersServicios import (
    AreaSerializer, CategoriaSerializer, ServicioSerializer,
    AreaListSerializer, CategoriaListSerializer, ServicioListSerializer
)


class AreaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar las áreas de servicios
    """
    queryset = Area.objects.all()
    serializer_class = AreaSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ["nombre"]
    ordering_fields = ["nombre", "id", "created_at"]
    ordering = ["nombre"]
    filterset_fields = ["activo"]
    
    def get_serializer_class(self):
        """
        Usar serializer simplificado para listados
        """
        if self.action == 'list':
            return AreaListSerializer
        return AreaSerializer
    
    def get_queryset(self):
        """
        Optimizar consultas y aplicar filtros por defecto
        """
        queryset = Area.objects.all()
        
        # Filtrar solo activos por defecto si no se especifica lo contrario
        activo = self.request.query_params.get('activo', None)
        if activo is None:
            # Si no se especifica activo, mostrar solo los activos por defecto
            queryset = queryset.filter(activo=True)
        
        return queryset.order_by('nombre')


class CategoriaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar las categorías de servicios
    """
    queryset = Categoria.objects.select_related("area").all()
    serializer_class = CategoriaSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ["nombre", "area__nombre"]
    ordering_fields = ["nombre", "area__nombre", "id", "created_at"]
    ordering = ["area__nombre", "nombre"]
    filterset_fields = ["activo", "area"]
    
    def get_serializer_class(self):
        """
        Usar serializer simplificado para listados
        """
        if self.action == 'list':
            return CategoriaListSerializer
        return CategoriaSerializer
    
    def get_queryset(self):
        """
        Optimizar consultas y aplicar filtros por defecto
        """
        queryset = Categoria.objects.select_related("area").all()
        
        # Filtrar por área si se especifica
        area_id = self.request.query_params.get('area', None)
        if area_id:
            queryset = queryset.filter(area_id=area_id)
        
        # Filtrar solo activos por defecto si no se especifica lo contrario
        activo = self.request.query_params.get('activo', None)
        if activo is None:
            queryset = queryset.filter(activo=True)
        
        return queryset.order_by('area__nombre', 'nombre')


class ServicioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar los servicios
    """
    queryset = Servicio.objects.select_related("categoria", "categoria__area").all()
    serializer_class = ServicioSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ["nombre", "descripcion", "categoria__nombre", "categoria__area__nombre"]
    ordering_fields = ["nombre", "precio", "id", "created_at"]
    ordering = ["nombre"]
    filterset_fields = ["activo", "categoria", "categoria__area"]
    
    def get_serializer_class(self):
        """
        Usar serializer simplificado para listados
        """
        if self.action == 'list':
            return ServicioListSerializer
        return ServicioSerializer
    
    def get_queryset(self):
        """
        Optimizar consultas y aplicar filtros por defecto
        """
        queryset = Servicio.objects.select_related("categoria", "categoria__area").all()
        
        # Filtrar por área si se especifica
        area_id = self.request.query_params.get('area', None)
        if area_id:
            queryset = queryset.filter(categoria__area_id=area_id)
        
        # Filtrar por categoría si se especifica
        categoria_id = self.request.query_params.get('categoria', None)
        if categoria_id:
            queryset = queryset.filter(categoria_id=categoria_id)
        
        # Filtrar solo activos por defecto si no se especifica lo contrario
        activo = self.request.query_params.get('activo', None)
        if activo is None:
            queryset = queryset.filter(activo=True)
        
        return queryset.order_by('categoria__area__nombre', 'categoria__nombre', 'nombre')
    
    def destroy(self, request, *args, **kwargs):
        """
        Implementar borrado lógico en lugar de borrado físico
        """
        instance = self.get_object()
        instance.activo = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def create(self, request, *args, **kwargs):
        """
        Personalizar respuesta de creación
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, 
            status=status.HTTP_201_CREATED, 
            headers=headers
        )
    
    def update(self, request, *args, **kwargs):
        """
        Personalizar respuesta de actualización
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}
        
        return Response(serializer.data)
