from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .modelsVehiculos import Vehiculo, Marca, Modelo
from personal_admin.views import registrar_bitacora
from personal_admin.models import Bitacora
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
        
        user_tenant = self.request.user.profile.tenant
        
        queryset = Vehiculo.objects.filter(
            tenant=user_tenant
        ).select_related('cliente', 'marca', 'modelo')
        
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
    
    def create(self, request, *args, **kwargs):
        user_tenant = request.user.profile.tenant
        
        data = request.data.copy()
        data['tenant'] = user_tenant.id
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            instance = serializer.save(tenant=user_tenant)
        except Exception as e:
            # Capturar error de placa duplicada (unique_together)
            if 'vehiculo_numero_placa_tenant_id' in str(e):
                return Response(
                    {"numero_placa": ["Ya existe un vehículo con este número de placa en su taller."]}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            # Si es otro error, muéstralo
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        """Crear un nuevo vehículo con registro en bitácora"""
        headers = self.get_success_headers(serializer.data)
        response = Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        
        if response.status_code == status.HTTP_201_CREATED:
            # Obtener el vehículo creado usando el serializer para obtener el ID
            vehiculo_id = response.data.get('id') or response.data.get('pk')
            if vehiculo_id:
                vehiculo = Vehiculo.objects.get(id=vehiculo_id)
                marca_nombre = vehiculo.marca.nombre if vehiculo.marca else "Sin marca"
                modelo_nombre = vehiculo.modelo.nombre if vehiculo.modelo else "Sin modelo"
                cliente_nombre = f"{vehiculo.cliente.nombre} {vehiculo.cliente.apellido}" if vehiculo.cliente else "Sin cliente"
                
                descripcion = f"Vehículo '{vehiculo.numero_placa}' creado - Marca: {marca_nombre}, Modelo: {modelo_nombre}, Cliente: {cliente_nombre}, Color: {vehiculo.color or 'No especificado'}, Año: {vehiculo.año or 'No especificado'}"
                
                registrar_bitacora(
                    usuario=request.user,
                    accion=Bitacora.Accion.CREAR,
                    modulo=Bitacora.Modulo.VEHICULO,
                    descripcion=descripcion,
                    request=request
                )
        
        return response
    
    def update(self, request, *args, **kwargs):
        """Actualizar un vehículo con registro en bitácora"""
        # Obtener el ID del vehículo antes de la actualización
        vehiculo_id = kwargs.get('pk')
        
        response = super().update(request, *args, **kwargs)
        
        if response.status_code == status.HTTP_200_OK and vehiculo_id:
            try:
                # Obtener el vehículo actualizado desde la base de datos
                vehiculo = Vehiculo.objects.get(id=vehiculo_id)
                marca_nombre = vehiculo.marca.nombre if vehiculo.marca else "Sin marca"
                modelo_nombre = vehiculo.modelo.nombre if vehiculo.modelo else "Sin modelo"
                cliente_nombre = f"{vehiculo.cliente.nombre} {vehiculo.cliente.apellido}" if vehiculo.cliente else "Sin cliente"
                
                descripcion = f"Vehículo '{vehiculo.numero_placa}' actualizado - Marca: {marca_nombre}, Modelo: {modelo_nombre}, Cliente: {cliente_nombre}, Color: {vehiculo.color or 'No especificado'}, Año: {vehiculo.año or 'No especificado'}"
                
                registrar_bitacora(
                    usuario=request.user,
                    accion=Bitacora.Accion.EDITAR,
                    modulo=Bitacora.Modulo.VEHICULO,
                    descripcion=descripcion,
                    request=request
                )
            except Vehiculo.DoesNotExist:
                # Si no se puede obtener el vehículo, no registrar en bitácora
                pass
        
        return response
    
    def destroy(self, request, *args, **kwargs):
        """Eliminar un vehículo con registro en bitácora"""
        vehiculo = self.get_object()
        placa = vehiculo.numero_placa
        marca_nombre = vehiculo.marca.nombre if vehiculo.marca else "Sin marca"
        modelo_nombre = vehiculo.modelo.nombre if vehiculo.modelo else "Sin modelo"
        cliente_nombre = f"{vehiculo.cliente.nombre} {vehiculo.cliente.apellido}" if vehiculo.cliente else "Sin cliente"
        
        response = super().destroy(request, *args, **kwargs)
        
        if response.status_code == status.HTTP_204_NO_CONTENT:
            descripcion = f"Vehículo '{placa}' eliminado - Marca: {marca_nombre}, Modelo: {modelo_nombre}, Cliente: {cliente_nombre}, Color: {vehiculo.color or 'No especificado'}, Año: {vehiculo.año or 'No especificado'}"
            
            registrar_bitacora(
                usuario=request.user,
                accion=Bitacora.Accion.ELIMINAR,
                modulo=Bitacora.Modulo.VEHICULO,
                descripcion=descripcion,
                request=request
            )
        
        return response
    
    @action(detail=False, methods=['get'])
    def marcas(self, request):
        """
        Endpoint para obtener todas las marcas disponibles.
        Útil para autocompletado en el frontend.
        """
        user_tenant = request.user.profile.tenant
        marcas = Marca.objects.filter(tenant=user_tenant).order_by('nombre')
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
        user_tenant = request.user.profile.tenant
        
        modelos = Modelo.objects.filter(tenant=user_tenant).select_related('marca')
        
        # Filtro por marca si se proporciona
        marca_id = request.query_params.get('marca_id', None)
        if marca_id:
            modelos = modelos.filter(marca_id=marca_id)
        
        modelos = modelos.order_by('marca__nombre', 'nombre')
        serializer = ModeloSerializer(modelos, many=True)
        return Response(serializer.data)
    
