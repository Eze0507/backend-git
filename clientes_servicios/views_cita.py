from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.utils import timezone
from datetime import datetime, time, timezone as dt_timezone
import logging

logger = logging.getLogger(__name__)
from .models import Cliente, Cita
from .serializers.serializer_cita_cliente import (
    CitaClienteSerializer,
    CitaClienteCreateSerializer
)
from personal_admin.views import registrar_bitacora
from personal_admin.models import Bitacora
from personal_admin.models import Empleado


class CitaClienteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para que los clientes gestionen sus citas.
    - Clientes solo ven sus propias citas (las que agendaron + las que les agendaron empleados)
    - Clientes pueden crear nuevas citas
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['vehiculo__numero_placa', 'descripcion', 'tipo_cita']
    ordering_fields = ['fecha_hora_inicio', 'fecha_creacion', 'estado']
    ordering = ['-fecha_creacion']  # Más recientes primero por fecha de creación
    
    def get_serializer_class(self):
        """Usar serializer completo para lectura y simplificado para creación"""
        if self.action == 'create':
            return CitaClienteCreateSerializer
        return CitaClienteSerializer
    
    def get_queryset(self):
        """Filtrar citas para mostrar solo las del cliente autenticado"""
        user = self.request.user
        user_tenant = user.profile.tenant
        try:
            cliente = Cliente.objects.get(usuario=user, activo=True, tenant=user_tenant)
        except Cliente.DoesNotExist:
            return Cita.objects.none()

        queryset = Cita.objects.filter(
            tenant=user_tenant
        ).select_related(
            'cliente', 'empleado', 'vehiculo'
        ).prefetch_related('cliente__usuario')
        
        queryset = queryset.filter(cliente=cliente)

        # Filtros opcionales
        estado = self.request.query_params.get('estado', None)
        if estado:
            queryset = queryset.filter(estado=estado)

        fecha_desde = self.request.query_params.get('fecha_desde', None)
        if fecha_desde:
            try:
                fecha_desde = datetime.fromisoformat(fecha_desde.replace('Z', '+00:00'))
                if timezone.is_naive(fecha_desde):
                    fecha_desde = timezone.make_aware(fecha_desde, dt_timezone.utc)
                queryset = queryset.filter(fecha_hora_inicio__gte=fecha_desde)
            except (ValueError, AttributeError):
                pass

        fecha_hasta = self.request.query_params.get('fecha_hasta', None)
        if fecha_hasta:
            try:
                fecha_hasta = datetime.fromisoformat(fecha_hasta.replace('Z', '+00:00'))
                if timezone.is_naive(fecha_hasta):
                    fecha_hasta = timezone.make_aware(fecha_hasta, dt_timezone.utc)
                queryset = queryset.filter(fecha_hora_inicio__lte=fecha_hasta)
            except (ValueError, AttributeError):
                pass

        return queryset
    
    def create(self, request, *args, **kwargs):
        user = request.user
        
        user_tenant = user.profile.tenant
        
        try:
            cliente = Cliente.objects.get(usuario=user, activo=True, tenant=user_tenant)
        except Cliente.DoesNotExist:
            return Response(
                {'error': 'No se encontró un perfil de cliente asociado a este usuario.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().create(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        """Crear cita y asignar automáticamente el cliente del usuario autenticado"""
        user = self.request.user
        
        user_tenant = user.profile.tenant
        
        cliente = Cliente.objects.get(usuario=user, activo=True, tenant=user_tenant)

        vehiculo = serializer.validated_data.get('vehiculo')
        if vehiculo.cliente != cliente or vehiculo.tenant != user_tenant:
            raise ValidationError({
                'vehiculo': 'El vehículo seleccionado no pertenece a tu cuenta.'
            })

        # Crear confirmada por defecto cuando la crea el cliente
        instance = serializer.save(cliente=cliente, estado='confirmada', tenant=user_tenant)

        cliente_nombre = f"{instance.cliente.nombre} {instance.cliente.apellido}".strip()
        vehiculo_info = f" - Vehículo: {instance.vehiculo.numero_placa}" if instance.vehiculo else ""
        empleado_info = f" - Empleado: {instance.empleado.nombre} {instance.empleado.apellido}" if instance.empleado else ""
        descripcion = f"Cita agendada por cliente '{cliente_nombre}'{vehiculo_info}{empleado_info}. Tipo: {instance.get_tipo_cita_display()}, Fecha: {instance.fecha_hora_inicio}"

        registrar_bitacora(
            usuario=user,
            accion=Bitacora.Accion.CREAR,
            modulo=Bitacora.Modulo.CITA,
            descripcion=descripcion,
            request=self.request
        )

    def destroy(self, request, *args, **kwargs):
        """Los clientes no pueden eliminar citas desde 'Mis Citas'."""
        return Response({'detail': 'Eliminación no permitida para clientes.'}, status=status.HTTP_403_FORBIDDEN)

    def update(self, request, *args, **kwargs):
        """Permitir que el cliente edite para reprogramar (fecha/hora) o cambiar estado."""
        instance = self.get_object()
        
        user_tenant = request.user.profile.tenant

        # Seguridad: solo propietario
        try:
            cliente = Cliente.objects.get(usuario=request.user, activo=True, tenant=user_tenant)
        except Cliente.DoesNotExist:
            return Response({'error': 'Perfil de cliente no encontrado.'}, status=status.HTTP_400_BAD_REQUEST)
        if instance.cliente_id != cliente.id:
            return Response({'detail': 'No autorizado.'}, status=status.HTTP_403_FORBIDDEN)

        # Filtrar campos permitidos
        allowed_fields = {'fecha_hora_inicio', 'fecha_hora_fin', 'estado', 'vehiculo', 'descripcion', 'nota'}
        data = {k: v for k, v in request.data.items() if k in allowed_fields}
        if not data:
            return Response({'detail': 'Sin cambios válidos.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validaciones básicas de horario similares al serializer de creación
        fecha_inicio = data.get('fecha_hora_inicio', None)
        fecha_fin = data.get('fecha_hora_fin', None)

        try:
            if isinstance(fecha_inicio, str):
                fecha_inicio = datetime.fromisoformat(fecha_inicio.replace('Z', '+00:00'))
            if isinstance(fecha_fin, str):
                fecha_fin = datetime.fromisoformat(fecha_fin.replace('Z', '+00:00'))
        except Exception:
            return Response({'detail': 'Formato de fecha inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        if fecha_inicio and timezone.is_naive(fecha_inicio):
            fecha_inicio = timezone.make_aware(fecha_inicio, dt_timezone.utc)
        if fecha_fin and timezone.is_naive(fecha_fin):
            fecha_fin = timezone.make_aware(fecha_fin, dt_timezone.utc)

        if fecha_inicio and fecha_fin:
            if fecha_fin <= fecha_inicio:
                return Response({'fecha_hora_fin': 'La fecha fin debe ser posterior al inicio.'}, status=status.HTTP_400_BAD_REQUEST)
            if fecha_inicio.date() != fecha_fin.date():
                return Response({'fecha_hora_fin': 'La cita debe iniciar y terminar el mismo día.'}, status=status.HTTP_400_BAD_REQUEST)
            duracion = fecha_fin - fecha_inicio
            if duracion.total_seconds() > 2 * 3600:
                return Response({'fecha_hora_fin': 'La duración máxima es de 2 horas.'}, status=status.HTTP_400_BAD_REQUEST)

            # Validar conflictos con otras citas del mismo empleado
            empleado = instance.empleado
            if empleado:
                conflicto = Cita.objects.filter(
                    empleado=empleado,
                    tenant=user_tenant,
                    estado__in=['pendiente', 'confirmada']
                ).exclude(id=instance.id).filter(
                    fecha_hora_inicio__lt=fecha_fin,
                    fecha_hora_fin__gt=fecha_inicio
                ).exists()
                if conflicto:
                    return Response({'fecha_hora_inicio': 'Horario ocupado con otra cita del empleado.'}, status=status.HTTP_400_BAD_REQUEST)

        # Aplicar cambios
        if fecha_inicio:
            instance.fecha_hora_inicio = fecha_inicio
        if fecha_fin:
            instance.fecha_hora_fin = fecha_fin
        if 'estado' in data:
            if data['estado'] not in ['pendiente', 'confirmada', 'cancelada']:
                return Response({'estado': 'Estado no permitido.'}, status=status.HTTP_400_BAD_REQUEST)
            instance.estado = data['estado']
        if 'vehiculo' in data:
            # DRF manejará por serializer; aquí asumimos id
            try:
                from operaciones_inventario.modelsVehiculos import Vehiculo
                if data['vehiculo'] is None:
                    instance.vehiculo = None
                else:
                    v = Vehiculo.objects.get(id=data['vehiculo'], tenant=user_tenant)
                    if v.cliente_id != cliente.id:
                        return Response({'vehiculo': 'El vehículo no pertenece a tu cuenta.'}, status=status.HTTP_400_BAD_REQUEST)
                    instance.vehiculo = v
            except Exception:
                return Response({'vehiculo': 'Vehículo inválido.'}, status=status.HTTP_400_BAD_REQUEST)
        if 'descripcion' in data:
            instance.descripcion = data['descripcion']
        if 'nota' in data:
            instance.nota = data['nota']

        instance.save()
        return Response(CitaClienteSerializer(instance).data, status=status.HTTP_200_OK)
    
    def _get_cliente_from_request(self, request):
        """Función helper para obtener el cliente y tenant de forma segura."""
        user = request.user
        user_tenant = user.profile.tenant
        try:
            cliente = Cliente.objects.get(usuario=user, activo=True, tenant=user_tenant)
            return cliente
        except Cliente.DoesNotExist:
            return None
    
    @action(detail=True, methods=['post'])
    def confirmar(self, request, pk=None):
        instance = self.get_object() # Ya filtrado por tenant
        cliente = self._get_cliente_from_request(request)
        if not cliente:
            return Response({'error': 'Perfil de cliente no encontrado.'}, status=status.HTTP_400_BAD_REQUEST)
        if instance.cliente_id != cliente.id:
            return Response({'detail': 'No autorizado.'}, status=status.HTTP_403_FORBIDDEN)
        
        instance.estado = 'confirmada'
        instance.save()
        return Response({'detail': 'Cita confirmada.'}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        instance = self.get_object() # Ya filtrado por tenant
        cliente = self._get_cliente_from_request(request)
        if not cliente:
            return Response({'error': 'Perfil de cliente no encontrado.'}, status=status.HTTP_400_BAD_REQUEST)
        if instance.cliente_id != cliente.id:
            return Response({'detail': 'No autorizado.'}, status=status.HTTP_403_FORBIDDEN)

        instance.estado = 'cancelada'
        instance.save()
        return Response({'detail': 'Cita cancelada.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def reprogramar(self, request, pk=None):
        """Cambiar horario de la cita (editar fecha/hora)."""
        # Reutiliza update con partial
        request._full_data = request.data
        kwargs = {'partial': True}
        return self.update(request, pk=pk, **kwargs)
    
    @action(detail=False, methods=['get'], url_path='mi-cliente-id')
    def mi_cliente_id(self, request):
        # NUEVO: Usar el helper
        cliente = self._get_cliente_from_request(request)
        if cliente:
            return Response({'cliente_id': cliente.id}, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'No se encontró un perfil de cliente asociado a este usuario.'},
                status=status.HTTP_404_NOT_FOUND
            )


# Vista separada fuera del ViewSet usando APIView para evitar problemas de routing
class CalendarioEmpleadoView(APIView):
    """
    Vista independiente para obtener calendario de empleado.
    Devuelve las citas activas del empleado, opcionalmente filtradas por día.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def get(self, request, empleado_id):
        user_tenant = request.user.profile.tenant
        try:
            empleado = Empleado.objects.get(id=empleado_id, estado=True, tenant=user_tenant)
        except Empleado.DoesNotExist:
            return Response(
                {'error': 'Empleado no encontrado o inactivo.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Permitir filtrar por un día específico (YYYY-MM-DD)
        dia_str = request.query_params.get('dia')
        if dia_str:
            try:
                # Construir rango de día en timezone-aware (UTC)
                dia_date = datetime.fromisoformat(dia_str).date()
                start_naive = datetime.combine(dia_date, time.min)
                end_naive = datetime.combine(dia_date, time.max)
                start_utc = timezone.make_aware(start_naive, dt_timezone.utc)
                end_utc = timezone.make_aware(end_naive, dt_timezone.utc)
                citas_ocupadas = Cita.objects.filter(
                    empleado=empleado,
                    tenant=user_tenant,
                    estado__in=['pendiente', 'confirmada'],
                ).filter(
                    fecha_hora_inicio__lt=end_utc,
                    fecha_hora_fin__gt=start_utc,
                ).order_by('fecha_hora_inicio')
            except Exception:
                # Si el parámetro es inválido, caer al comportamiento por defecto
                citas_ocupadas = Cita.objects.filter(
                    empleado=empleado,
                    tenant=user_tenant,
                    estado__in=['pendiente', 'confirmada']
                ).order_by('fecha_hora_inicio')
        else:
            citas_ocupadas = Cita.objects.filter(
                empleado=empleado,
                tenant=user_tenant,
                estado__in=['pendiente', 'confirmada']
            ).order_by('fecha_hora_inicio')
        
        # Serializar las fechas de inicio y fin en UTC
        horarios_ocupados = []
        for cita in citas_ocupadas:
            try:
                fecha_inicio = cita.fecha_hora_inicio
                fecha_fin = cita.fecha_hora_fin
                if not fecha_inicio or not fecha_fin:
                    continue
                # Normalizar a UTC
                if timezone.is_naive(fecha_inicio):
                    fecha_inicio_utc = timezone.make_aware(fecha_inicio, dt_timezone.utc)
                else:
                    fecha_inicio_utc = fecha_inicio.astimezone(dt_timezone.utc)
                if timezone.is_naive(fecha_fin):
                    fecha_fin_utc = timezone.make_aware(fecha_fin, dt_timezone.utc)
                else:
                    fecha_fin_utc = fecha_fin.astimezone(dt_timezone.utc)
                horarios_ocupados.append({
                    'fecha_hora_inicio': fecha_inicio_utc.isoformat(),
                    'fecha_hora_fin': fecha_fin_utc.isoformat(),
                    'ocupado': True
                })
            except Exception as e:
                # Silenciar errores de serialización en producción
                logger.debug(f"Calendario serialize error cita {getattr(cita,'id',None)}: {e}")
        
        return Response({
            'empleado_id': empleado.id,
            'empleado_nombre': f"{empleado.nombre} {empleado.apellido}",
            'horarios_ocupados': horarios_ocupados
        }, status=status.HTTP_200_OK)
