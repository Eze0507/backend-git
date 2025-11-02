from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, IntegerField
from .models import Cliente, Cita
from .serializers.serializer_cliente import ClienteSerializer
from .serializers.serializer_cita import CitaSerializer, CitaCreateSerializer
from personal_admin.views import registrar_bitacora
from personal_admin.models import Bitacora
from personal_admin.models import Empleado


class ClienteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar Clientes.
    - Listar con filtros y búsqueda
    - Borrado lógico
    """
    queryset = Cliente.objects.filter(activo=True).order_by('nombre', 'apellido')
    serializer_class = ClienteSerializer

    def perform_create(self, serializer):
        """Crear cliente y registrar en bitácora"""
        # Ejecutar la creación original
        instance = serializer.save()
        
        # Registrar en bitácora
        descripcion = f"Cliente '{instance.nombre} {instance.apellido}' creado con NIT '{instance.nit}' y tipo '{instance.tipo_cliente}'"
        
        registrar_bitacora(
            usuario=self.request.user,
            accion=Bitacora.Accion.CREAR,
            modulo=Bitacora.Modulo.CLIENTE,
            descripcion=descripcion,
            request=self.request
        )
    
    def perform_update(self, serializer):
        """Actualizar cliente y registrar en bitácora"""
        # Guardar datos originales para comparación
        instance = self.get_object()
        nombre_original = instance.nombre
        apellido_original = instance.apellido
        nit_original = instance.nit
        tipo_original = instance.tipo_cliente
        
        # Ejecutar la actualización original
        instance = serializer.save()
        
        # Crear descripción detallada
        cambios = []
        if instance.nombre != nombre_original:
            cambios.append(f"nombre: '{nombre_original}' → '{instance.nombre}'")
        if instance.apellido != apellido_original:
            cambios.append(f"apellido: '{apellido_original}' → '{instance.apellido}'")
        if instance.nit != nit_original:
            cambios.append(f"NIT: '{nit_original}' → '{instance.nit}'")
        if instance.tipo_cliente != tipo_original:
            cambios.append(f"tipo: '{tipo_original}' → '{instance.tipo_cliente}'")
        
        descripcion = f"Cliente '{instance.nombre} {instance.apellido}' (NIT: {instance.nit}) actualizado"
        if cambios:
            descripcion += f". Cambios: {', '.join(cambios)}"
        else:
            descripcion += ". Sin cambios detectados"
        
        registrar_bitacora(
            usuario=self.request.user,
            accion=Bitacora.Accion.EDITAR,
            modulo=Bitacora.Modulo.CLIENTE,
            descripcion=descripcion,
            request=self.request
        )
    
    def perform_destroy(self, instance):
        """Eliminar cliente (borrado lógico) y registrar en bitácora"""
        # Guardar información antes del borrado lógico
        nombre_cliente = instance.nombre
        apellido_cliente = instance.apellido
        nit_cliente = instance.nit
        tipo_cliente = instance.tipo_cliente
        
        # Ejecutar el borrado lógico original
        instance.activo = False
        instance.save()
        
        # Registrar en bitácora
        descripcion = f"Cliente '{nombre_cliente} {apellido_cliente}' (NIT: {nit_cliente}, tipo: {tipo_cliente}) eliminado (borrado lógico)"
        
        registrar_bitacora(
            usuario=self.request.user,
            accion=Bitacora.Accion.ELIMINAR,
            modulo=Bitacora.Modulo.CLIENTE,
            descripcion=descripcion,
            request=self.request
        )

    def destroy(self, request, *args, **kwargs):
        """Borrado lógico en lugar de delete físico"""
        instance = self.get_object()
        instance.activo = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CitaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar Citas.
    - Empleados: Solo ven las citas que ellos han creado (donde son el empleado asignado)
    - Administradores: Ven todas las citas
    """
    permission_classes = [IsAuthenticated]
    queryset = Cita.objects.all()  # Queryset por defecto
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['cliente__nombre', 'cliente__apellido', 'vehiculo__numero_placa', 'descripcion']
    ordering_fields = ['fecha_hora_inicio', 'fecha_creacion', 'estado']
    ordering = ['fecha_hora_inicio']
    
    def get_serializer_class(self):
        """Usar serializer completo para lectura y simplificado para creación"""
        if self.action == 'create':
            return CitaCreateSerializer
        return CitaSerializer
    
    def get_queryset(self):
        """
        Filtrar citas según el rol del usuario:
        - Administrador: Ve todas las citas
        - Empleado: Solo ve sus propias citas (donde es el empleado asignado)
        """
        user = self.request.user
        
        # Verificar si el usuario es administrador (tiene el grupo 'administrador')
        is_admin = user.groups.filter(name='administrador').exists()
        
        # Construir queryset base
        queryset = Cita.objects.select_related(
            'cliente', 'empleado'
        ).select_related('vehiculo').prefetch_related('cliente__usuario')
        
        # Si NO es administrador, filtrar por empleado
        if not is_admin:
            # Buscar el empleado por NOMBRE (no por usuario asociado)
            # Si el usuario autenticado es "pastor", buscar un empleado con nombre "pastor"
            # sin importar qué usuario esté asociado en el campo "usuario"
            empleado = Empleado.objects.filter(
                nombre__iexact=user.username,
                estado=True
            ).first()
            
            if empleado:
                # Solo mostrar citas donde este empleado está asignado
                queryset = queryset.filter(empleado=empleado)
            else:
                # Si no se encuentra el empleado por nombre, no mostrar citas
                queryset = queryset.none()
        
        # Filtros adicionales por query params
        estado = self.request.query_params.get('estado', None)
        if estado:
            queryset = queryset.filter(estado=estado)
        
        tipo_cita = self.request.query_params.get('tipo_cita', None)
        if tipo_cita:
            queryset = queryset.filter(tipo_cita=tipo_cita)
        
        # Filtro por rango de fechas
        fecha_desde = self.request.query_params.get('fecha_desde', None)
        if fecha_desde:
            queryset = queryset.filter(fecha_hora_inicio__gte=fecha_desde)
        
        fecha_hasta = self.request.query_params.get('fecha_hasta', None)
        if fecha_hasta:
            queryset = queryset.filter(fecha_hora_inicio__lte=fecha_hasta)
        
        # Filtro por cliente
        cliente_id = self.request.query_params.get('cliente_id', None)
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        
        # Filtro por vehículo
        vehiculo_id = self.request.query_params.get('vehiculo_id', None)
        if vehiculo_id:
            queryset = queryset.filter(vehiculo_id=vehiculo_id)
        
        return queryset
    
    def perform_create(self, serializer):
        """Crear cita y registrar en bitácora"""
        user = self.request.user
        
        # Crear la cita con el empleado que se especificó en el formulario
        instance = serializer.save()
        
        # Preparar información para bitácora
        is_admin = user.groups.filter(name='administrador').exists()
        if instance.empleado:
            creador_info = f" - Empleado asignado: {instance.empleado.nombre} {instance.empleado.apellido}"
        elif is_admin:
            creador_info = f" - Creada por administrador: {user.username}"
        else:
            creador_info = f" - Creada por: {user.username}"
        
        # Registrar en bitácora
        cliente_nombre = f"{instance.cliente.nombre} {instance.cliente.apellido}".strip()
        vehiculo_info = f" - Vehículo: {instance.vehiculo.numero_placa}" if instance.vehiculo else ""
        empleado_info = f" - Empleado asignado: {instance.empleado.nombre} {instance.empleado.apellido}" if instance.empleado else ""
        descripcion = f"Cita creada para cliente '{cliente_nombre}'{vehiculo_info}{empleado_info}{creador_info}. Tipo: {instance.get_tipo_cita_display()}, Fecha: {instance.fecha_hora_inicio}"
        
        registrar_bitacora(
            usuario=user,
            accion=Bitacora.Accion.CREAR,
            modulo=Bitacora.Modulo.CITA,
            descripcion=descripcion,
            request=self.request
        )
    
    def perform_update(self, serializer):
        """Actualizar cita y registrar en bitácora"""
        instance = serializer.save()
        
        cliente_nombre = f"{instance.cliente.nombre} {instance.cliente.apellido}".strip()
        descripcion = f"Cita #{instance.id} actualizada para cliente '{cliente_nombre}'. Nuevo estado: {instance.get_estado_display()}"
        
        registrar_bitacora(
            usuario=self.request.user,
            accion=Bitacora.Accion.EDITAR,
            modulo=Bitacora.Modulo.CITA,
            descripcion=descripcion,
            request=self.request
        )
    
    def perform_destroy(self, instance):
        """Eliminar cita y registrar en bitácora"""
        cliente_nombre = f"{instance.cliente.nombre} {instance.cliente.apellido}".strip()
        descripcion = f"Cita #{instance.id} eliminada para cliente '{cliente_nombre}'"
        
        instance.delete()
        
        registrar_bitacora(
            usuario=self.request.user,
            accion=Bitacora.Accion.ELIMINAR,
            modulo=Bitacora.Modulo.CITA,
            descripcion=descripcion,
            request=self.request
        )


