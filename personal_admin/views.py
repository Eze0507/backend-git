from django.shortcuts import render
from django.http import JsonResponse
from rest_framework import viewsets, status,filters, permissions,generics
from rest_framework.decorators import action
from .serializers.serializers_user import UserSerializer, GroupAuxSerializer
from django.db.models import ProtectedError
from .serializers.serializers_register import UserRegistrationSerializer
from django.contrib.auth.models import User, Group, Permission
from .models import Cargo, Bitacora, Asistencia
from .serializers.serializers_cargo import CargoSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.authentication import JWTAuthentication
from .serializers.serializers_rol import RoleSerializer, PermissionSerializer 
from rest_framework.permissions import IsAuthenticated, AllowAny 
from personal_admin.models import Empleado
from .serializers.serializers_empleado import EmpleadoReadSerializer, EmpleadoWriteSerializer
from clientes_servicios.models import Cliente
from personal_admin.serializers.serializers_profile import ProfileUpdateSerializer, EmpleadoProfileUpdateSerializer
from rest_framework import permissions
from rest_framework import status
from .serializers.serializers_password import ChangePasswordSerializer
from .serializers.serializers_bitacora import BitacoraSerializer
from rest_framework.exceptions import NotFound
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from .serializers.serializers_user import UserSerializer
from .models_saas import UserProfile, Tenant
from .serializers.serializers_tenant import TallerRegistrationSerializer
from .serializers.serializers_tenantProfile import TenantProfileSerializer
from .serializers.serializers_userInvit import ClienteRegistrationSerializer
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
import requests
from django.conf import settings
from django.db.models import Sum, Count, Q, DecimalField
from django.db.models.functions import TruncMonth, TruncDay
from datetime import datetime, timedelta, date
import calendar
from decimal import Decimal
from django.utils import timezone
import pytz

# ===== FUNCIÓN HELPER PARA REGISTRAR EN BITÁCORA =====
def registrar_bitacora(usuario, accion, modulo, descripcion, request=None):
    """
    Función helper para registrar acciones en la bitácora.
    
    Args:
        usuario: Usuario que realiza la acción
        accion: Acción realizada (Bitacora.Accion.CREAR, EDITAR, ELIMINAR, etc.)
        modulo: Módulo donde se realiza la acción (Bitacora.Modulo.CARGO, CLIENTE, etc.)
        descripcion: Descripción detallada de la acción
        request: Objeto request para obtener la IP (opcional)
    """
    ip_address = None
    if request:
        # Obtener IP del request
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
    
    user_tenant = None
    
    if usuario and usuario.is_authenticated and hasattr(usuario, 'profile'):
        user_tenant = usuario.profile.tenant
    
    Bitacora.objects.create(
        usuario=usuario,
        accion=accion,
        modulo=modulo,
        descripcion=descripcion,
        ip_address=ip_address,
        tenant=user_tenant
    )


# ---- ViewSets de tus compañeros ----
class UserViewSet(viewsets.ModelViewSet):

    serializer_class = UserSerializer
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user_tenant = self.request.user.profile.tenant
        return User.objects.filter(
            profile__tenant=user_tenant
        ).order_by('username')

    def perform_create(self, serializer):
        """Crear usuario y registrar en bitácora"""
        # Ejecutar la creación original
        instance = serializer.save()
        
        try:
            user_tenant = self.request.user.profile.tenant
            UserProfile.objects.create(usuario=instance, tenant=user_tenant)

        except Exception as e:
            print(f"Error asignando tenant al profile del nuevo usuario: {e}")
        
        # Obtener información del rol
        rol_info = instance.groups.first()
        rol_nombre = rol_info.name if rol_info else 'Sin rol'
        
        # Registrar en bitácora
        descripcion = f"Usuario '{instance.username}' creado con email '{instance.email}' y rol '{rol_nombre}'"
        
        registrar_bitacora(
            usuario=self.request.user,
            accion=Bitacora.Accion.CREAR,
            modulo=Bitacora.Modulo.AUTENTICACION,
            descripcion=descripcion,
            request=self.request
        )
    
    def perform_update(self, serializer):
        """Actualizar usuario y registrar en bitácora"""
        # Guardar datos originales para comparación
        instance = self.get_object()
        username_original = instance.username
        email_original = instance.email
        rol_original = instance.groups.first()
        rol_original_nombre = rol_original.name if rol_original else 'Sin rol'
        
        # Ejecutar la actualización original
        instance = serializer.save()
        
        # Obtener nuevos datos
        rol_nuevo = instance.groups.first()
        rol_nuevo_nombre = rol_nuevo.name if rol_nuevo else 'Sin rol'
        
        # Crear descripción detallada
        cambios = []
        if instance.username != username_original:
            cambios.append(f"username: '{username_original}' → '{instance.username}'")
        if instance.email != email_original:
            cambios.append(f"email: '{email_original}' → '{instance.email}'")
        if rol_original_nombre != rol_nuevo_nombre:
            cambios.append(f"rol: '{rol_original_nombre}' → '{rol_nuevo_nombre}'")
        
        descripcion = f"Usuario '{instance.username}' actualizado"
        if cambios:
            descripcion += f". Cambios: {', '.join(cambios)}"
        else:
            descripcion += ". Sin cambios detectados"
        
        registrar_bitacora(
            usuario=self.request.user,
            accion=Bitacora.Accion.EDITAR,
            modulo=Bitacora.Modulo.AUTENTICACION,
            descripcion=descripcion,
            request=self.request
        )
    
    def perform_destroy(self, instance):
        """Eliminar usuario y registrar en bitácora"""
        # Guardar información antes de eliminar
        username_usuario = instance.username
        email_usuario = instance.email
        rol_info = instance.groups.first()
        rol_nombre = rol_info.name if rol_info else 'Sin rol'
        
        # Ejecutar la eliminación original
        instance.delete()
        
        # Registrar en bitácora
        descripcion = f"Usuario '{username_usuario}' eliminado. Tenía email '{email_usuario}' y rol '{rol_nombre}'"
        
        registrar_bitacora(
            usuario=self.request.user,
            accion=Bitacora.Accion.ELIMINAR,
            modulo=Bitacora.Modulo.AUTENTICACION,
            descripcion=descripcion,
            request=self.request
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError:
            return Response(
                {"detail": "No se puede eliminar este usuario porque está asociado a otros registros (como un cliente o empleado)."},
                status=status.HTTP_400_BAD_REQUEST
            )



class GroupAuxViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupAuxSerializer


class UserRegistrationView(APIView):
    permission_classes = [AllowAny] # <-- Añadido para permitir el acceso sin autenticación

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Es mejor práctica devolver un mensaje de éxito en lugar de los datos del usuario.
            return Response(
                {"message": f"Usuario '{user.username}' creado exitosamente."},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    """Vista para cerrar sesión - invalida el refresh token"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()  # Invalida el token
                
                # Registrar LOGOUT en bitácora
                registrar_bitacora(
                    usuario=request.user,
                    accion=Bitacora.Accion.LOGOUT,
                    modulo=Bitacora.Modulo.AUTENTICACION,
                    descripcion=f"Usuario {request.user.username} cerró sesión exitosamente",
                    request=request
                )
                
                return Response(
                    {"message": "Sesión cerrada exitosamente"}, 
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"error": "Token de refresh requerido"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except TokenError:
            return Response(
                {"error": "Token inválido"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": "Error al cerrar sesión"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CargoViewSet(viewsets.ModelViewSet):
    serializer_class = CargoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user_tenant = self.request.user.profile.tenant
        return Cargo.objects.filter(tenant=user_tenant)
    
    def perform_create(self, serializer):
        user_tenant = self.request.user.profile.tenant
        instance = serializer.save(tenant=user_tenant)

# ---- ViewSets para Roles y Permisos ----
class RoleViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = RoleSerializer
    
    def perform_create(self, serializer):
        """Crear rol y registrar en bitácora"""
        # Ejecutar la creación original
        instance = serializer.save()
        
        # Registrar en bitácora
        permisos_info = [perm.name for perm in instance.permissions.all()]
        descripcion = f"Rol '{instance.name}' creado con permisos: {', '.join(permisos_info) if permisos_info else 'Sin permisos'}"
        
        registrar_bitacora(
            usuario=self.request.user,
            accion=Bitacora.Accion.CREAR,
            modulo=Bitacora.Modulo.AUTENTICACION,
            descripcion=descripcion,
            request=self.request
        )
    
    def perform_update(self, serializer):
        """Actualizar rol y registrar en bitácora"""
        # Guardar datos originales para comparación
        instance = self.get_object()
        nombre_original = instance.name
        permisos_originales = set(instance.permissions.values_list('name', flat=True))
        
        # Ejecutar la actualización original
        instance = serializer.save()
        
        # Obtener nuevos permisos
        permisos_nuevos = set(instance.permissions.values_list('name', flat=True))
        
        # Crear descripción detallada
        permisos_agregados = permisos_nuevos - permisos_originales
        permisos_removidos = permisos_originales - permisos_nuevos
        
        descripcion = f"Rol '{instance.name}' actualizado"
        if permisos_agregados:
            descripcion += f". Permisos agregados: {', '.join(permisos_agregados)}"
        if permisos_removidos:
            descripcion += f". Permisos removidos: {', '.join(permisos_removidos)}"
        if not permisos_agregados and not permisos_removidos:
            descripcion += ". Sin cambios en permisos"
        
        registrar_bitacora(
            usuario=self.request.user,
            accion=Bitacora.Accion.EDITAR,
            modulo=Bitacora.Modulo.AUTENTICACION,
            descripcion=descripcion,
            request=self.request
        )
    
    def perform_destroy(self, instance):
        """Eliminar rol y registrar en bitácora"""
        # Guardar información antes de eliminar
        nombre_rol = instance.name
        permisos_info = [perm.name for perm in instance.permissions.all()]
        
        # Ejecutar la eliminación original
        instance.delete()
        
        # Registrar en bitácora
        descripcion = f"Rol '{nombre_rol}' eliminado. Tenía permisos: {', '.join(permisos_info) if permisos_info else 'Sin permisos'}"
        
        registrar_bitacora(
            usuario=self.request.user,
            accion=Bitacora.Accion.ELIMINAR,
            modulo=Bitacora.Modulo.AUTENTICACION,
            descripcion=descripcion,
            request=self.request
        )

class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer


#viewset para actualizar perfil cliente y empleado
class UserProfileView(APIView):
    """Vista unificada para obtener el perfil del usuario autenticado"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Intentar encontrar si es empleado
        try:
            empleado = Empleado.objects.get(usuario=user)
            serializer = EmpleadoProfileUpdateSerializer(empleado)
            return Response({
                'type': 'empleado',
                'data': serializer.data
            })
        except Empleado.DoesNotExist:
            pass
        
        # Intentar encontrar si es cliente
        try:
            cliente = Cliente.objects.get(usuario=user)
            serializer = ProfileUpdateSerializer(cliente)
            return Response({
                'type': 'cliente', 
                'data': serializer.data
            })
        except Cliente.DoesNotExist:
            pass
            
        # Si no es ni empleado ni cliente
        return Response({
            'error': 'Usuario sin perfil asociado',
            'detail': 'El usuario no tiene un perfil de empleado o cliente'
        }, status=status.HTTP_404_NOT_FOUND)

class ClienteProfileUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Cliente.objects.all()
    serializer_class = ProfileUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        try:
            return Cliente.objects.get(usuario=self.request.user)
        except Cliente.DoesNotExist:
            raise NotFound("No existe perfil de cliente para este usuario.")
            
    def handle_exception(self, exc):
        """Manejar excepciones de manera más amigable"""
        if isinstance(exc, NotFound):
            return Response(
                {"error": "Perfil no encontrado", "detail": str(exc)},
                status=status.HTTP_404_NOT_FOUND
            )
        return super().handle_exception(exc)

class EmpleadoProfileUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = EmpleadoProfileUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        try:
            return Empleado.objects.get(usuario=self.request.user)
        except Empleado.DoesNotExist:
            raise NotFound("No existe perfil de empleado para este usuario.")
            
    def handle_exception(self, exc):
        """Manejar excepciones de manera más amigable"""
        if isinstance(exc, NotFound):
            return Response(
                {"error": "Perfil no encontrado", "detail": str(exc)},
                status=status.HTTP_404_NOT_FOUND
            )
        return super().handle_exception(exc)

#viewset cambio de contraseña
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            # Verificar si la contraseña actual es correcta
            if not user.check_password(serializer.data.get("old_password")):
                return Response(
                    {"old_password": ["Contraseña incorrecta."]}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Establecer la nueva contraseña
            user.set_password(serializer.data.get("new_password"))
            user.save()
            return Response({"detail": "Contraseña actualizada exitosamente."}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# ---- Tu nuevo ViewSet para Empleados ----
class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_authenticated

class EmpleadoViewSet(viewsets.ModelViewSet):
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]  
    search_fields = ["nombre", "apellido", "ci", "telefono"]
    ordering_fields = ["apellido", "nombre", "ci", "fecha_registro", "sueldo"]
    ordering = ["apellido", "nombre"]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user_tenant = self.request.user.profile.tenant
        return Empleado.objects.filter(
            tenant=user_tenant
        ).select_related('cargo', 'usuario')
    
    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return EmpleadoWriteSerializer
        return EmpleadoReadSerializer
    
    def perform_create(self, serializer):
        """Crear empleado y registrar en bitácora"""
        user_tenant = self.request.user.profile.tenant
        # Ejecutar la creación original
        instance = serializer.save(tenant=user_tenant)
        
        # Registrar en bitácora
        cargo_nombre = instance.cargo.nombre if instance.cargo else 'Sin cargo'
        descripcion = f"Empleado '{instance.nombre} {instance.apellido}' creado con CI '{instance.ci}' y cargo '{cargo_nombre}'"
        
        registrar_bitacora(
            usuario=self.request.user,
            accion=Bitacora.Accion.CREAR,
            modulo=Bitacora.Modulo.EMPLEADO,
            descripcion=descripcion,
            request=self.request
        )
    
    def perform_update(self, serializer):
        """Actualizar empleado y registrar en bitácora"""
        # Guardar datos originales para comparación
        instance = self.get_object()
        nombre_original = instance.nombre
        apellido_original = instance.apellido
        ci_original = instance.ci
        cargo_original = instance.cargo.nombre if instance.cargo else 'Sin cargo'
        sueldo_original = instance.sueldo
        
        # Ejecutar la actualización original
        instance = serializer.save()
        
        # Obtener nuevos datos
        cargo_nuevo = instance.cargo.nombre if instance.cargo else 'Sin cargo'
        
        # Crear descripción detallada
        cambios = []
        if instance.nombre != nombre_original:
            cambios.append(f"nombre: '{nombre_original}' → '{instance.nombre}'")
        if instance.apellido != apellido_original:
            cambios.append(f"apellido: '{apellido_original}' → '{instance.apellido}'")
        if instance.ci != ci_original:
            cambios.append(f"CI: '{ci_original}' → '{instance.ci}'")
        if cargo_original != cargo_nuevo:
            cambios.append(f"cargo: '{cargo_original}' → '{cargo_nuevo}'")
        if instance.sueldo != sueldo_original:
            cambios.append(f"sueldo: ${sueldo_original} → ${instance.sueldo}")
        
        descripcion = f"Empleado '{instance.nombre} {instance.apellido}' (CI: {instance.ci}) actualizado"
        if cambios:
            descripcion += f". Cambios: {', '.join(cambios)}"
        else:
            descripcion += ". Sin cambios detectados"
        
        registrar_bitacora(
            usuario=self.request.user,
            accion=Bitacora.Accion.EDITAR,
            modulo=Bitacora.Modulo.EMPLEADO,
            descripcion=descripcion,
            request=self.request
        )
    
    def perform_destroy(self, instance):
        """Eliminar empleado y registrar en bitácora"""
        # Guardar información antes de eliminar
        nombre_empleado = instance.nombre
        apellido_empleado = instance.apellido
        ci_empleado = instance.ci
        cargo_info = instance.cargo.nombre if instance.cargo else 'Sin cargo'
        sueldo_info = instance.sueldo
        
        # Ejecutar la eliminación original
        instance.delete()
        
        # Registrar en bitácora
        descripcion = f"Empleado '{nombre_empleado} {apellido_empleado}' (CI: {ci_empleado}, cargo: {cargo_info}, sueldo: ${sueldo_info}) eliminado"
        
        registrar_bitacora(
            usuario=self.request.user,
            accion=Bitacora.Accion.ELIMINAR,
            modulo=Bitacora.Modulo.EMPLEADO,
            descripcion=descripcion,
            request=self.request
        )

@method_decorator(csrf_exempt, name='dispatch')
class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        # Obtener el username antes de la autenticación
        username = request.data.get('username', 'Usuario desconocido')
        
        # Llamar al método post original para autenticar
        response = super().post(request, *args, **kwargs)
        
        # Si la autenticación fue exitosa (status 200), registrar en bitácora
        if response.status_code == 200:
            try:
                # Obtener el usuario autenticado
                user = User.objects.get(username=username)
                # Registrar LOGIN en bitácora
                registrar_bitacora(
                    usuario=user,
                    accion=Bitacora.Accion.LOGIN,
                    modulo=Bitacora.Modulo.AUTENTICACION,
                    descripcion=f"Usuario {username} inició sesión exitosamente",
                    request=request
                )
            except User.DoesNotExist:
                # Si no se encuentra el usuario, registrar con información limitada
                registrar_bitacora(
                    usuario=None,  # No hay usuario autenticado aún
                    accion=Bitacora.Accion.LOGIN,
                    modulo=Bitacora.Modulo.AUTENTICACION,
                    descripcion=f"Intento de login con username: {username}",
                    request=request
                )
            except Exception as e:
                # No fallar la autenticación por errores en bitácora
                print(f"Error al registrar login en bitácora: {e}")
        
        return response

@method_decorator(ensure_csrf_cookie, name='dispatch')
class CSRFTokenView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({ "detail": "CSRF cookie set" })

# ---- Función auxiliar para obtener IP ----
def get_client_ip(request):
    """
    Obtiene la dirección IP del cliente desde el request.
    Maneja proxies y headers de X-Forwarded-For.
    """
    if not request:
        return None
    
    # Verificar headers de proxy
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    
    return ip

# ---- Función para registrar bitácora ----
def registrar_bitacora(usuario, accion, modulo, descripcion, request=None, ip_address=None):
    """
    Función para registrar acciones en la bitácora del sistema.
    
    Args:
        usuario: Instancia del modelo User o None (para casos como LOGIN)
        accion: String con la acción realizada (CREAR, EDITAR, ELIMINAR, LOGIN, LOGOUT)
        modulo: String con el módulo afectado (Cargo, Cliente, Empleado, Vehiculo, Autenticacion)
        descripcion: String con descripción detallada de la acción
        request: Objeto request de Django (opcional, para obtener IP automáticamente)
        ip_address: String con la dirección IP (opcional, si no se proporciona request)
    
    Returns:
        bool: True si se registró exitosamente, False si hubo error
    """
    try:
        # Si usuario es None, crear un usuario temporal para el registro
        if usuario is None:
            # Crear o obtener un usuario temporal para registros sin usuario autenticado
            usuario_temp, created = User.objects.get_or_create(
                username='SISTEMA',
                defaults={
                    'email': 'sistema@taller.com',
                    'first_name': 'Sistema',
                    'last_name': 'Bitácora',
                    'is_active': False  # Usuario inactivo, solo para bitácora
                }
            )
            usuario = usuario_temp
        
        # Obtener IP address
        if not ip_address and request:
            ip_address = get_client_ip(request)
        
        user_tenant = None
        
        if usuario and usuario.is_authenticated and hasattr(usuario, 'profile'):
            user_tenant = usuario.profile.tenant
        
        Bitacora.objects.create(
            usuario=usuario,
            accion=accion,
            modulo=modulo,
            descripcion=descripcion,
            ip_address=ip_address,
            tenant=user_tenant
        )
        return True
    except Exception as e:
        # Log del error para debugging, pero no debe fallar la operación principal
        print(f"Error al registrar bitácora: {e}")
        return False

# ---- ViewSet para consultar Bitácora ----
class BitacoraViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para consultar registros de bitácora.
    Permite filtrar por usuario, módulo, acción y fecha.
    """
    serializer_class = BitacoraSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['descripcion', 'usuario__username', 'usuario__email', 'ip_address']
    ordering_fields = ['fecha_accion', 'usuario__username', 'modulo', 'accion']
    ordering = ['-fecha_accion']  # Más recientes primero
    
    
    def get_queryset(self):
        """Filtros personalizados para la bitácora"""
        
        user_tenant = self.request.user.profile.tenant
        
        queryset = Bitacora.objects.filter(
            tenant=user_tenant
        ).select_related('usuario')
        
        # Filtro por módulo
        modulo = self.request.query_params.get('modulo', None)
        if modulo:
            queryset = queryset.filter(modulo=modulo)
        
        # Filtro por acción
        accion = self.request.query_params.get('accion', None)
        if accion:
            queryset = queryset.filter(accion=accion)
        
        # Filtro por usuario
        usuario_id = self.request.query_params.get('usuario', None)
        if usuario_id:
            queryset = queryset.filter(usuario_id=usuario_id)
        
        # Filtro por IP
        ip_filter = self.request.query_params.get('ip_filter', None)
        if ip_filter:
            queryset = queryset.filter(ip_address__icontains=ip_filter)
        
        # Filtro por fecha desde
        fecha_desde = self.request.query_params.get('fecha_desde', None)
        if fecha_desde:
            queryset = queryset.filter(fecha_accion__date__gte=fecha_desde)
        
        # Filtro por fecha hasta
        fecha_hasta = self.request.query_params.get('fecha_hasta', None)
        if fecha_hasta:
            queryset = queryset.filter(fecha_accion__date__lte=fecha_hasta)
        
        return queryset


class MeView(APIView):
    """Devuelve información básica del usuario autenticado (username, email, names)"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

class TallerRegistrationView(APIView):
    """
    API pública para registrar un NUEVO Taller (Tenant).
    Crea el Taller, el Usuario Propietario y el UserProfile.
    """
    permission_classes = [AllowAny] 

    def post(self, request):
        serializer = TallerRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save() 
            return Response(
                {"message": f"Taller y usuario '{user.username}' creados exitosamente."},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TenantProfileView(RetrieveUpdateAPIView):
    serializer_class = TenantProfileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self):
        return self.request.user.profile.tenant
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        data = request.data.copy()
        logo_file = request.FILES.get("logo_file")

        if logo_file:
            url = "https://api.imgbb.com/1/upload"
            payload = {"key": settings.API_KEY_IMGBB}
            files = {"image": logo_file.read()}
            
            try:
                response = requests.post(url, data=payload, files=files)
                response.raise_for_status() 
                
                if response.status_code == 200:
                    image_url = response.json()["data"]["url"]
                    data["logo"] = image_url
                else:
                    return Response(
                        {"error": "Error al subir el logo a ImgBB"}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            except requests.exceptions.RequestException as e:
                return Response(
                    {"error": f"Error de conexión con ImgBB: {str(e)}"}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        partial = kwargs.pop('partial', False)
        
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer) 

        return Response(serializer.data)

class ClienteRegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ClienteRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save() 
            
            return Response(
                {"message": f"Cliente '{user.username}' creado exitosamente."},
                status=status.HTTP_201_CREATED
            )
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ===== DASHBOARD ENDPOINTS =====
class DashboardAdminView(APIView):
    """
    Vista para obtener estadísticas del dashboard para administradores.
    Incluye datos generales del taller: ingresos, órdenes, clientes, empleados, servicios.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        user_tenant = user.profile.tenant
        
        # Verificar que sea administrador
        is_admin = user.groups.filter(name='administrador').exists()
        if not is_admin:
            return Response(
                {"error": "No tiene permisos para acceder a esta vista"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Importar modelos necesarios
        from operaciones_inventario.modelsOrdenTrabajo import OrdenTrabajo
        from finanzas_facturacion.models import Pago
        from clientes_servicios.models import Cita
        from operaciones_inventario.modelsItem import Item
        
        # Estadísticas generales
        total_clientes = Cliente.objects.filter(tenant=user_tenant, activo=True).count()
        total_empleados = Empleado.objects.filter(tenant=user_tenant, estado=True).count()
        total_ordenes = OrdenTrabajo.objects.filter(tenant=user_tenant).count()
        
        # Ingresos
        pagos_completados = Pago.objects.filter(
            orden_trabajo__tenant=user_tenant,
            estado='completado'
        )
        ingresos_totales = pagos_completados.aggregate(
            total=Sum('monto', output_field=DecimalField())
        )['total'] or Decimal('0.00')
        
        # Obtener fecha actual con zona horaria de Bolivia (America/La_Paz)
        tz_bolivia = pytz.timezone('America/La_Paz')
        ahora_utc = timezone.now()
        ahora_bolivia = ahora_utc.astimezone(tz_bolivia)
        
        # Ingresos del mes actual (en Bolivia)
        mes_actual_bolivia = ahora_bolivia.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        ingresos_mes = Pago.objects.filter(
            orden_trabajo__tenant=user_tenant,
            estado='completado',
            fecha_pago__gte=mes_actual_bolivia
        ).aggregate(
            total=Sum('monto', output_field=DecimalField())
        )['total'] or Decimal('0.00')
        
        # Ingresos últimos 6 meses para gráfico (usando fecha de Bolivia)
        # Calcular los últimos 6 meses desde la fecha actual de Bolivia
        ingresos_por_mes = Pago.objects.filter(
            orden_trabajo__tenant=user_tenant,
            estado='completado'
        ).annotate(
            mes=TruncMonth('fecha_pago')
        ).values('mes').annotate(
            total=Sum('monto', output_field=DecimalField())
        ).order_by('mes')
        
        # Convertir a diccionario para facilitar búsqueda
        ingresos_dict = {}
        for item in ingresos_por_mes:
            if item['mes']:
                mes_str = item['mes'].strftime('%Y-%m')
                ingresos_dict[mes_str] = float(item['total'] or 0)
        
        # Generar datos para los últimos 6 meses (desde la fecha actual de Bolivia)
        ingresos_mensuales = []
        fecha_actual_bolivia = ahora_bolivia.date()
        año_actual = fecha_actual_bolivia.year
        mes_actual = fecha_actual_bolivia.month
        
        # Calcular los últimos 6 meses correctamente (incluyendo el mes actual)
        # Desde hace 5 meses hasta el mes actual (total 6 meses)
        for i in range(5, -1, -1):  # i va de 5 a 0
            # Calcular el mes objetivo: mes_actual - i
            # Si mes_actual = 11 (noviembre) y i = 0, entonces mes_objetivo = 11 (noviembre) ✓
            # Si mes_actual = 11 y i = 1, entonces mes_objetivo = 10 (octubre) ✓
            mes_objetivo = mes_actual - i
            año_objetivo = año_actual
            
            # Ajustar si el mes es negativo o cero (cambio de año hacia atrás)
            if mes_objetivo <= 0:
                mes_objetivo += 12
                año_objetivo -= 1
            
            mes_str = f"{año_objetivo}-{mes_objetivo:02d}"
            ingresos_mensuales.append({
                'mes': mes_str,
                'total': ingresos_dict.get(mes_str, 0.0)
            })
        
        # Órdenes por estado
        ordenes_por_estado = OrdenTrabajo.objects.filter(
            tenant=user_tenant
        ).values('estado').annotate(
            cantidad=Count('id')
        )
        
        estados_ordenes = {item['estado']: item['cantidad'] for item in ordenes_por_estado}
        
        # Servicios más utilizados (items más usados en órdenes)
        servicios_mas_usados = Item.objects.filter(
            detalles_orden__orden_trabajo__tenant=user_tenant,
            detalles_orden__orden_trabajo__estado__in=['finalizada', 'entregada']
        ).annotate(
            veces_usado=Count('detalles_orden')
        ).order_by('-veces_usado')[:5]
        
        servicios_data = [
            {
                'nombre': servicio.nombre,
                'nombre_corto': servicio.nombre[:30] + '...' if len(servicio.nombre) > 30 else servicio.nombre,
                'veces_usado': servicio.veces_usado
            }
            for servicio in servicios_mas_usados
        ]
        
        # Órdenes recientes (últimas 5)
        ordenes_recientes = OrdenTrabajo.objects.filter(
            tenant=user_tenant
        ).select_related('cliente', 'vehiculo').order_by('-fecha_creacion')[:5]
        
        ordenes_recientes_data = [
            {
                'id': orden.id,
                'cliente': f"{orden.cliente.nombre} {orden.cliente.apellido}".strip(),
                'estado': orden.estado,
                'total': float(orden.total),
                'fecha': orden.fecha_creacion.strftime('%Y-%m-%d') if orden.fecha_creacion else ''
            }
            for orden in ordenes_recientes
        ]
        
        # Citas pendientes
        citas_pendientes = Cita.objects.filter(
            tenant=user_tenant,
            estado__in=['pendiente', 'confirmada']
        ).count()
        
        return Response({
            'estadisticas': {
                'total_clientes': total_clientes,
                'total_empleados': total_empleados,
                'total_ordenes': total_ordenes,
                'ingresos_totales': float(ingresos_totales),
                'ingresos_mes_actual': float(ingresos_mes),
                'citas_pendientes': citas_pendientes
            },
            'graficos': {
                'ingresos_mensuales': ingresos_mensuales,
                'ordenes_por_estado': estados_ordenes,
                'servicios_mas_usados': servicios_data
            },
            'ordenes_recientes': ordenes_recientes_data
        }, status=status.HTTP_200_OK)


class DashboardEmpleadoView(APIView):
    """
    Vista para obtener estadísticas del dashboard para empleados.
    Muestra información relevante para el empleado: sus citas, órdenes asignadas, etc.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        user_tenant = user.profile.tenant
        
        # Verificar que sea empleado
        is_empleado = user.groups.filter(name='empleado').exists()
        if not is_empleado:
            return Response(
                {"error": "No tiene permisos para acceder a esta vista"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Obtener el empleado asociado al usuario
        try:
            empleado = Empleado.objects.get(usuario=user, tenant=user_tenant)
        except Empleado.DoesNotExist:
            return Response(
                {"error": "No se encontró perfil de empleado"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Importar modelos necesarios
        from clientes_servicios.models import Cita
        from operaciones_inventario.modelsOrdenTrabajo import OrdenTrabajo, AsignacionTecnico
        
        # Obtener fecha actual con zona horaria de Bolivia (America/La_Paz)
        tz_bolivia = pytz.timezone('America/La_Paz')
        ahora_utc = timezone.now()
        ahora_bolivia = ahora_utc.astimezone(tz_bolivia)
        hoy_date = ahora_bolivia.date()
        
        # Inicio y fin del día en Bolivia
        hoy_inicio = tz_bolivia.localize(datetime.combine(hoy_date, datetime.min.time()))
        hoy_fin = tz_bolivia.localize(datetime.combine(hoy_date, datetime.max.time()))
        
        # ===== CITAS =====
        # Todas las citas del empleado (sin filtro de estado para mostrar todas)
        todas_las_citas = Cita.objects.filter(
            empleado=empleado,
            tenant=user_tenant
        ).select_related('cliente', 'vehiculo').order_by('fecha_hora_inicio')
        
        # Total de citas del empleado
        total_citas = todas_las_citas.count()
        
        # Citas de hoy - usar rango de fechas en zona horaria de Bolivia
        citas_hoy_queryset = todas_las_citas.filter(
            fecha_hora_inicio__gte=hoy_inicio,
            fecha_hora_inicio__lte=hoy_fin
        )
        
        citas_hoy = citas_hoy_queryset.count()
        
        # Datos de citas de hoy
        citas_hoy_data = [
            {
                'id': cita.id,
                'cliente': f"{cita.cliente.nombre} {cita.cliente.apellido}".strip(),
                'tipo': cita.get_tipo_cita_display(),
                'fecha_hora': cita.fecha_hora_inicio.isoformat() if cita.fecha_hora_inicio else '',
                'estado': cita.estado
            }
            for cita in citas_hoy_queryset
        ]
        
        # Citas de la semana (desde el inicio de la semana hasta el fin)
        inicio_semana = hoy_date - timedelta(days=hoy_date.weekday())
        fin_semana = inicio_semana + timedelta(days=6)
        inicio_semana_datetime = tz_bolivia.localize(datetime.combine(inicio_semana, datetime.min.time()))
        fin_semana_datetime = tz_bolivia.localize(datetime.combine(fin_semana, datetime.max.time()))
        
        citas_semana = todas_las_citas.filter(
            fecha_hora_inicio__gte=inicio_semana_datetime,
            fecha_hora_inicio__lte=fin_semana_datetime
        ).count()
        
        # Próximas citas (las próximas 5 citas después de ahora en Bolivia)
        proximas_citas = todas_las_citas.filter(
            fecha_hora_inicio__gte=ahora_bolivia
        ).order_by('fecha_hora_inicio')[:5]
        
        proximas_citas_data = [
            {
                'id': cita.id,
                'cliente': f"{cita.cliente.nombre} {cita.cliente.apellido}".strip(),
                'tipo': cita.get_tipo_cita_display(),
                'fecha_hora': cita.fecha_hora_inicio.isoformat() if cita.fecha_hora_inicio else '',
                'estado': cita.estado
            }
            for cita in proximas_citas
        ]
        
        # ===== ÓRDENES =====
        # Mostrar TODAS las órdenes del taller (no solo las asignadas al empleado)
        ordenes_asignadas_queryset = OrdenTrabajo.objects.filter(
            tenant=user_tenant
        ).select_related('cliente', 'vehiculo').prefetch_related('asignaciones_tecnicos')
        
        # Total de órdenes del taller
        total_ordenes = ordenes_asignadas_queryset.count()
        
        # Órdenes por estado
        ordenes_en_proceso = ordenes_asignadas_queryset.filter(estado='en_proceso').count()
        ordenes_pendientes = ordenes_asignadas_queryset.filter(estado='pendiente').count()
        ordenes_finalizadas = ordenes_asignadas_queryset.filter(estado='finalizada').count()
        ordenes_entregadas = ordenes_asignadas_queryset.filter(estado='entregada').count()
        
        # Órdenes recientes (últimas 10, ordenadas por fecha de creación descendente)
        ordenes_recientes = ordenes_asignadas_queryset.order_by('-fecha_creacion')[:10]
        
        ordenes_recientes_data = [
            {
                'id': orden.id,
                'cliente': f"{orden.cliente.nombre} {orden.cliente.apellido}".strip(),
                'estado': orden.estado,
                'fecha': orden.fecha_creacion.strftime('%Y-%m-%d') if orden.fecha_creacion else '',
                'total': float(orden.total) if orden.total else 0.0
            }
            for orden in ordenes_recientes
        ]
        
        return Response({
            'estadisticas': {
                'citas_hoy': citas_hoy,
                'citas_semana': citas_semana,
                'total_citas': total_citas,
                'total_ordenes': total_ordenes,
                'ordenes_en_proceso': ordenes_en_proceso,
                'ordenes_pendientes': ordenes_pendientes,
                'ordenes_finalizadas': ordenes_finalizadas,
                'ordenes_entregadas': ordenes_entregadas
            },
            'citas_hoy': citas_hoy_data,
            'proximas_citas': proximas_citas_data,
            'ordenes_recientes': ordenes_recientes_data
        }, status=status.HTTP_200_OK)


# ===== ASISTENCIA ENDPOINTS =====
from .serializers.serializers_asistencia import (
    AsistenciaReadSerializer, 
    AsistenciaWriteSerializer, 
    AsistenciaMarcarSerializer
)

class AsistenciaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar asistencias.
    - Administradores: Ven todas las asistencias
    - Empleados: Pueden marcar su propia asistencia
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = AsistenciaReadSerializer
    
    def get_queryset(self):
        user = self.request.user
        try:
            user_tenant = user.profile.tenant
        except AttributeError:
            return Asistencia.objects.none()
        
        # Verificar que sea administrador
        is_admin = user.groups.filter(name='administrador').exists()
        if not is_admin:
            return Asistencia.objects.none()
        
        # CRÍTICO: Filtrar SOLO por tenant del admin - así aparecen todas las asistencias marcadas por empleados
        queryset = Asistencia.objects.filter(tenant=user_tenant).select_related('empleado', 'tenant')
        
        # Log para verificar
        import logging
        logger = logging.getLogger(__name__)
        total_asistencias = queryset.count()
        logger.info(f"[ASISTENCIAS VIEWSET] Admin: {user.username}, Tenant: {user_tenant.id}, Total asistencias en tenant: {total_asistencias}")
        
        # Filtros opcionales
        fecha = self.request.query_params.get('fecha', None)
        empleado_id = self.request.query_params.get('empleado_id', None)
        estado = self.request.query_params.get('estado', None)
        
        # Si se especifica fecha, filtrar por esa fecha
        # Si NO se especifica fecha, mostrar todas las asistencias del tenant
        if fecha:
            try:
                # Intentar parsear la fecha
                fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha=fecha_obj)
            except (ValueError, TypeError):
                # Si la fecha es inválida, ignorar el filtro
                pass
        
        if empleado_id:
            try:
                queryset = queryset.filter(empleado_id=int(empleado_id))
            except (ValueError, TypeError):
                pass
        
        if estado:
            queryset = queryset.filter(estado=estado)
        
        # Ordenar por fecha descendente (más recientes primero), luego por fecha_creacion descendente (últimas marcadas arriba - pila LIFO), y luego por empleado
        # Esto hace que cuando un empleado marca asistencia, aparezca arriba de las anteriores del mismo día
        return queryset.order_by('-fecha', '-fecha_creacion', '-fecha_actualizacion', 'empleado__apellido', 'empleado__nombre')
    
    def list(self, request, *args, **kwargs):
        """
        Lista personalizada para debug y mejor manejo de asistencias.
        """
        user = request.user
        user_tenant = None
        try:
            user_tenant = user.profile.tenant
        except AttributeError:
            return Response({"error": "Usuario no tiene perfil asociado"}, status=status.HTTP_400_BAD_REQUEST)
        
        queryset = self.filter_queryset(self.get_queryset())
        
        # DEBUG: Imprimir información útil
        import logging
        logger = logging.getLogger(__name__)
        total_en_tenant = Asistencia.objects.filter(tenant=user_tenant).count()
        total_sin_tenant = Asistencia.objects.filter(tenant__isnull=True).count()
        total_en_queryset = queryset.count()
        
        logger.info(f"[ASISTENCIAS] Admin: {user.username}, Tenant: {user_tenant.id if user_tenant else 'None'}")
        logger.info(f"[ASISTENCIAS] Total en tenant: {total_en_tenant}, Sin tenant: {total_sin_tenant}, En queryset filtrado: {total_en_queryset}")
        
        # Si no hay resultados, devolver información útil pero SIEMPRE con formato correcto
        if not queryset.exists():
            logger.warning(f"[ASISTENCIAS VIEWSET] ⚠️ No hay asistencias - Total en tenant: {total_en_tenant}, Sin tenant: {total_sin_tenant}")
            return Response({
                "count": 0,
                "results": [],
                "debug_info": {
                    "total_asistencias_en_tenant": total_en_tenant,
                    "total_asistencias_sin_tenant": total_sin_tenant,
                    "tenant_id": user_tenant.id if user_tenant else None,
                    "filtros_aplicados": {
                        "fecha": request.query_params.get('fecha', None),
                        "empleado_id": request.query_params.get('empleado_id', None),
                        "estado": request.query_params.get('estado', None),
                    },
                    "mensaje": "No hay asistencias registradas para los filtros seleccionados"
                }
            }, status=status.HTTP_200_OK)
        
        # Serializar los datos
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        
        logger.info(f"[ASISTENCIAS VIEWSET] Serializando {len(data)} asistencias")
        
        # Si hay paginación, usar la respuesta paginada
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            logger.info(f"[ASISTENCIAS VIEWSET] Respuesta paginada: {len(serializer.data)} items")
            return response
        
        # Si no hay paginación, devolver como objeto con results (compatible con frontend)
        # El queryset ya está ordenado por fecha y fecha_creacion descendente (pila LIFO)
        logger.info(f"[ASISTENCIAS VIEWSET] ✅ Respuesta sin paginación: {len(data)} items")
        logger.info(f"[ASISTENCIAS VIEWSET] Primeras 3 asistencias: {[{'id': d.get('id'), 'empleado': d.get('nombre_empleado'), 'fecha': d.get('fecha'), 'fecha_creacion': d.get('fecha_creacion')} for d in data[:3]]}")
        return Response({
            "count": len(data),
            "results": data
        }, status=status.HTTP_200_OK)
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return AsistenciaWriteSerializer
        return AsistenciaReadSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        try:
            context['tenant'] = self.request.user.profile.tenant
        except AttributeError:
            context['tenant'] = None
        return context
    
    
    
    def perform_create(self, serializer):
        try:
            user_tenant = self.request.user.profile.tenant
        except AttributeError:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"error": "Usuario no tiene perfil asociado. Contacte al administrador."})
        serializer.save(tenant=user_tenant)
        registrar_bitacora(
            self.request.user,
            Bitacora.Accion.CREAR,
            Bitacora.Modulo.ASISTENCIA,
            f"Asistencia creada para {serializer.instance.empleado} el {serializer.instance.fecha}",
            self.request
        )
    
    def perform_update(self, serializer):
        instance = serializer.save()
        registrar_bitacora(
            self.request.user,
            Bitacora.Accion.EDITAR,
            Bitacora.Modulo.ASISTENCIA,
            f"Asistencia actualizada para {instance.empleado} el {instance.fecha}",
            self.request
        )


# Vista separada para marcar asistencia con csrf_exempt
@method_decorator(csrf_exempt, name='dispatch')
class MarcarAsistenciaView(APIView):
    """
    Vista para que cualquier usuario autenticado marque entrada o salida.
    Usa csrf_exempt para evitar problemas con CSRF en aplicaciones móviles.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        
        # Obtener tenant (igual que en crear cita) - con protección
        try:
            user_tenant = user.profile.tenant
        except AttributeError:
            return Response(
                {"error": "Usuario no tiene perfil asociado. Contacte al administrador."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener tipo
        tipo = request.data.get('tipo', '').lower()
        if tipo not in ['entrada', 'salida']:
            return Response({"error": "tipo debe ser 'entrada' o 'salida'"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Buscar o crear empleado (igual que en crear cita - perform_create)
        empleado = None
        try:
            empleado = Empleado.objects.get(usuario=user, estado=True, tenant=user_tenant)
        except Empleado.DoesNotExist:
            try:
                empleado = Empleado.objects.get(usuario=user, estado=True)
                empleado.tenant = user_tenant
                empleado.save()
            except Empleado.DoesNotExist:
                # Crear empleado automáticamente
                from .models import Cargo
                cargo = Cargo.objects.filter(tenant=user_tenant).first()
                if not cargo:
                    cargo = Cargo.objects.create(
                        nombre="Empleado",
                        descripcion="Cargo por defecto",
                        sueldo=0.00,
                        tenant=user_tenant
                    )
                
                empleado = Empleado.objects.create(
                    usuario=user,
                    tenant=user_tenant,
                    cargo=cargo,
                    nombre=user.first_name or user.username,
                    apellido=user.last_name or "",
                    ci=user.username,
                    sueldo=0.00,
                    estado=True
                )
        
        # Fecha y hora actual en zona horaria de Bolivia
        tz_bolivia = pytz.timezone('America/La_Paz')
        ahora = datetime.now(tz_bolivia)
        fecha = ahora.date()
        hora = ahora.time()
        
        # Validar que sea día laboral (lunes a viernes)
        dia_semana = ahora.weekday()  # 0 = lunes, 6 = domingo
        if dia_semana >= 5:  # 5 = sábado, 6 = domingo
            dia_nombre = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][dia_semana]
            return Response({
                "error": f"No se puede marcar asistencia los fines de semana. Hoy es {dia_nombre}."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # MARCAR ENTRADA
        if tipo == 'entrada':
            # IMPORTANTE: Usar update_or_create con tenant para asegurar que siempre se guarde
            asistencia, created = Asistencia.objects.update_or_create(
                empleado=empleado,
                fecha=fecha,
                tenant=user_tenant,
                defaults={
                    'hora_entrada': hora,
                    'tenant': user_tenant  # CRÍTICO: Asegurar tenant explícitamente
                }
            )
            
            # Verificación adicional: SIEMPRE asegurar que el tenant esté correcto
            if asistencia.tenant != user_tenant:
                asistencia.tenant = user_tenant
                asistencia.hora_entrada = hora
                asistencia.save()
            
            # Verificar que el empleado tenga el tenant correcto
            if empleado.tenant != user_tenant:
                empleado.tenant = user_tenant
                empleado.save()
            
            # Log para verificar
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"[MARCAR ASISTENCIA] ✅ Entrada - Empleado: {empleado.id} ({empleado.nombre}), Tenant: {asistencia.tenant.id}, Fecha: {fecha}, Hora: {hora}")
            
            # Refrescar desde la BD
            asistencia.refresh_from_db()
            
            return Response({
                "success": True,
                "mensaje": "Entrada marcada correctamente",
                "fecha": fecha.isoformat(),
                "hora_entrada": asistencia.hora_entrada.strftime('%H:%M:%S') if asistencia.hora_entrada else None,
                "hora_salida": asistencia.hora_salida.strftime('%H:%M:%S') if asistencia.hora_salida else None,
                "estado": asistencia.estado,
                "empleado": f"{empleado.nombre} {empleado.apellido}",
                "empleado_id": empleado.id
            }, status=status.HTTP_200_OK)
        
        # MARCAR SALIDA
        asistencia = Asistencia.objects.filter(
            empleado=empleado,
            fecha=fecha,
            tenant=user_tenant
        ).first()
        
        if not asistencia:
            return Response({"error": "Debe marcar entrada primero"}, status=status.HTTP_400_BAD_REQUEST)
        
        # CRÍTICO: Asegurar que el tenant esté guardado
        if asistencia.tenant != user_tenant:
            asistencia.tenant = user_tenant
        
        asistencia.hora_salida = hora
        asistencia.save()  # El modelo calcula automáticamente horas_extras, horas_faltantes y estado
        
        # Log para verificar
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[MARCAR ASISTENCIA] ✅ Salida - Empleado: {empleado.id} ({empleado.nombre}), Tenant: {asistencia.tenant.id}, Fecha: {fecha}, Hora: {hora}, Estado: {asistencia.estado}")
        
        # Refrescar desde la BD para obtener datos calculados
        asistencia.refresh_from_db()
        
        # Calcular horas trabajadas totales (datetime ya está importado al inicio del archivo)
        entrada_dt = datetime.combine(fecha, asistencia.hora_entrada)
        salida_dt = datetime.combine(fecha, asistencia.hora_salida)
        if salida_dt < entrada_dt:
            salida_dt += timedelta(days=1)
        diferencia = salida_dt - entrada_dt
        horas_trabajadas = round(diferencia.total_seconds() / 3600.0, 2)
        
        return Response({
            "success": True,
            "mensaje": "Salida marcada correctamente",
            "fecha": fecha.isoformat(),
            "hora_entrada": asistencia.hora_entrada.strftime('%H:%M:%S') if asistencia.hora_entrada else None,
            "hora_salida": hora.strftime('%H:%M:%S'),
            "horas_trabajadas": horas_trabajadas,
            "horas_extras": float(asistencia.horas_extras) if asistencia.horas_extras else 0.00,
            "horas_faltantes": float(asistencia.horas_faltantes) if asistencia.horas_faltantes else 0.00,
            "estado": asistencia.estado,
            "empleado": f"{empleado.nombre} {empleado.apellido}",
            "empleado_id": empleado.id
        }, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
class MiAsistenciaView(APIView):
    """
    Vista para que un empleado vea su propia asistencia del día actual.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Obtener tenant
        try:
            user_tenant = user.profile.tenant
        except AttributeError:
            return Response(
                {"error": "Usuario no tiene perfil asociado."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Buscar empleado
        try:
            empleado = Empleado.objects.get(usuario=user, estado=True, tenant=user_tenant)
        except Empleado.DoesNotExist:
            try:
                empleado = Empleado.objects.get(usuario=user, estado=True)
                empleado.tenant = user_tenant
                empleado.save()
            except Empleado.DoesNotExist:
                return Response(
                    {"error": "No se encontró perfil de empleado."},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Obtener fecha actual
        tz_bolivia = pytz.timezone('America/La_Paz')
        ahora = datetime.now(tz_bolivia)
        fecha = ahora.date()
        
        # Buscar asistencia del día
        try:
            asistencia = Asistencia.objects.get(
                empleado=empleado,
                fecha=fecha,
                tenant=user_tenant
            )
            
            return Response({
                "id": asistencia.id,
                "fecha": asistencia.fecha.isoformat(),
                "hora_entrada": asistencia.hora_entrada.strftime('%H:%M:%S') if asistencia.hora_entrada else None,
                "hora_salida": asistencia.hora_salida.strftime('%H:%M:%S') if asistencia.hora_salida else None,
                "horas_extras": str(asistencia.horas_extras) if asistencia.horas_extras else "0.00",
                "horas_faltantes": str(asistencia.horas_faltantes) if asistencia.horas_faltantes else "0.00",
                "estado": asistencia.estado,
                "empleado": {
                    "id": empleado.id,
                    "nombre": empleado.nombre,
                    "apellido": empleado.apellido
                }
            }, status=status.HTTP_200_OK)
        except Asistencia.DoesNotExist:
            return Response({
                "id": None,
                "fecha": fecha.isoformat(),
                "hora_entrada": None,
                "hora_salida": None,
                "horas_extras": "0.00",
                "horas_faltantes": "0.00",
                "estado": "incompleto",
                "empleado": {
                    "id": empleado.id,
                    "nombre": empleado.nombre,
                    "apellido": empleado.apellido
                }
            }, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
class DiagnosticoAsistenciasView(APIView):
    """
    Endpoint de diagnóstico para verificar el estado de las asistencias.
    Solo para administradores.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Verificar que sea administrador
        is_admin = user.groups.filter(name='administrador').exists()
        if not is_admin:
            return Response(
                {"error": "Solo administradores pueden acceder a este endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            user_tenant = user.profile.tenant
        except AttributeError:
            return Response(
                {"error": "Usuario no tiene perfil asociado"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Estadísticas
        total_asistencias = Asistencia.objects.count()
        asistencias_en_tenant = Asistencia.objects.filter(tenant=user_tenant).count()
        asistencias_sin_tenant = Asistencia.objects.filter(tenant__isnull=True).count()
        asistencias_otros_tenants = Asistencia.objects.exclude(tenant=user_tenant).exclude(tenant__isnull=True).count()
        
        # Últimas 10 asistencias del tenant
        ultimas_asistencias = Asistencia.objects.filter(tenant=user_tenant).select_related('empleado', 'tenant').order_by('-fecha', '-fecha_creacion')[:10]
        
        # Últimas 10 asistencias sin tenant (para verificar problemas)
        ultimas_sin_tenant = Asistencia.objects.filter(tenant__isnull=True).select_related('empleado').order_by('-fecha', '-fecha_creacion')[:10]
        
        return Response({
            "tenant_id": user_tenant.id,
            "tenant_nombre": user_tenant.nombre if hasattr(user_tenant, 'nombre') else str(user_tenant),
            "estadisticas": {
                "total_asistencias": total_asistencias,
                "asistencias_en_tenant": asistencias_en_tenant,
                "asistencias_sin_tenant": asistencias_sin_tenant,
                "asistencias_otros_tenants": asistencias_otros_tenants,
            },
            "ultimas_asistencias_tenant": [
                {
                    "id": a.id,
                    "empleado": f"{a.empleado.nombre} {a.empleado.apellido}",
                    "empleado_id": a.empleado.id,
                    "fecha": a.fecha.isoformat(),
                    "hora_entrada": a.hora_entrada.strftime('%H:%M:%S') if a.hora_entrada else None,
                    "hora_salida": a.hora_salida.strftime('%H:%M:%S') if a.hora_salida else None,
                    "tenant_id": a.tenant.id if a.tenant else None,
                    "estado": a.estado,
                }
                for a in ultimas_asistencias
            ],
            "ultimas_sin_tenant": [
                {
                    "id": a.id,
                    "empleado": f"{a.empleado.nombre} {a.empleado.apellido}",
                    "empleado_id": a.empleado.id,
                    "fecha": a.fecha.isoformat(),
                    "hora_entrada": a.hora_entrada.strftime('%H:%M:%S') if a.hora_entrada else None,
                    "hora_salida": a.hora_salida.strftime('%H:%M:%S') if a.hora_salida else None,
                    "tenant_id": None,
                    "estado": a.estado,
                }
                for a in ultimas_sin_tenant
            ]
        }, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
class MiHistorialAsistenciaView(APIView):
    """
    Vista para que un empleado vea su historial de asistencias.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Obtener tenant
        try:
            user_tenant = user.profile.tenant
        except AttributeError:
            return Response(
                {"error": "Usuario no tiene perfil asociado."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Buscar empleado
        try:
            empleado = Empleado.objects.get(usuario=user, estado=True, tenant=user_tenant)
        except Empleado.DoesNotExist:
            try:
                empleado = Empleado.objects.get(usuario=user, estado=True)
                empleado.tenant = user_tenant
                empleado.save()
            except Empleado.DoesNotExist:
                return Response(
                    {"error": "No se encontró perfil de empleado."},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Obtener parámetros opcionales
        fecha_desde = request.query_params.get('fecha_desde', None)
        fecha_hasta = request.query_params.get('fecha_hasta', None)
        limite = int(request.query_params.get('limite', 30))  # Por defecto 30 días
        
        # Construir queryset
        queryset = Asistencia.objects.filter(
            empleado=empleado,
            tenant=user_tenant
        ).order_by('-fecha')
        
        # Aplicar filtros de fecha
        if fecha_desde:
            try:
                fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha__gte=fecha_desde_obj)
            except ValueError:
                pass
        
        if fecha_hasta:
            try:
                fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha__lte=fecha_hasta_obj)
            except ValueError:
                pass
        
        # Si no hay filtros de fecha, limitar a los últimos N días
        if not fecha_desde and not fecha_hasta:
            fecha_limite = datetime.now().date() - timedelta(days=limite)
            queryset = queryset.filter(fecha__gte=fecha_limite)
        
        # Obtener asistencias
        asistencias = queryset[:50]  # Máximo 50 registros
        
        # Serializar
        data = []
        for asistencia in asistencias:
            data.append({
                "id": asistencia.id,
                "fecha": asistencia.fecha.isoformat(),
                "hora_entrada": asistencia.hora_entrada.strftime('%H:%M:%S') if asistencia.hora_entrada else None,
                "hora_salida": asistencia.hora_salida.strftime('%H:%M:%S') if asistencia.hora_salida else None,
                "horas_extras": str(asistencia.horas_extras) if asistencia.horas_extras else "0.00",
                "horas_faltantes": str(asistencia.horas_faltantes) if asistencia.horas_faltantes else "0.00",
                "estado": asistencia.estado,
                "fecha_creacion": asistencia.fecha_creacion.isoformat() if asistencia.fecha_creacion else None,
            })
        
        return Response({
            "success": True,
            "count": len(data),
            "data": data
        }, status=status.HTTP_200_OK)


class AsistenciaReporteMensualView(APIView):
    """
    Vista para generar reporte mensual de asistencias (solo para administradores).
    Útil para pasar a nómina.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        user_tenant = user.profile.tenant
        
        # Verificar que sea administrador
        is_admin = user.groups.filter(name='administrador').exists()
        if not is_admin:
            return Response(
                {"error": "No tiene permisos para acceder a esta vista"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Obtener parámetros de fecha
        año = request.query_params.get('año', None)
        mes = request.query_params.get('mes', None)
        
        # Si no se proporcionan, usar el mes actual
        if not año or not mes:
            tz_bolivia = pytz.timezone('America/La_Paz')
            ahora_bolivia = datetime.now(tz_bolivia)
            año = ahora_bolivia.year
            mes = ahora_bolivia.month
        
        try:
            año = int(año)
            mes = int(mes)
        except (ValueError, TypeError):
            return Response(
                {"error": "Año y mes deben ser números válidos"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener todas las asistencias del mes
        asistencias = Asistencia.objects.filter(
            tenant=user_tenant,
            fecha__year=año,
            fecha__month=mes
        ).select_related('empleado').order_by('empleado__apellido', 'empleado__nombre', 'fecha')

        # Calcular días hábiles del mes (lunes a viernes)
        dias_habiles_mes = 0
        ultimo_dia = calendar.monthrange(año, mes)[1]
        for dia in range(1, ultimo_dia + 1):
            fecha_actual = date(año, mes, dia)
            if fecha_actual.weekday() < 5:  # 0-4 = lunes a viernes
                dias_habiles_mes += 1
        
        # Agrupar por empleado
        reporte_por_empleado = {}
        for asistencia in asistencias:
            empleado_id = asistencia.empleado.id
            if empleado_id not in reporte_por_empleado:
                reporte_por_empleado[empleado_id] = {
                    'empleado': {
                        'id': asistencia.empleado.id,
                        'nombre': asistencia.empleado.nombre,
                        'apellido': asistencia.empleado.apellido,
                        'ci': asistencia.empleado.ci
                    },
                    'asistencias': [],
                    'total_horas_extras': Decimal('0.00'),
                    'total_horas_faltantes': Decimal('0.00'),
                    'dias_completos': 0,
                    'dias_incompletos': 0,
                    'dias_extras': 0
                }
            
            reporte_por_empleado[empleado_id]['asistencias'].append({
                'fecha': asistencia.fecha.isoformat(),
                'hora_entrada': asistencia.hora_entrada.strftime('%H:%M:%S') if asistencia.hora_entrada else None,
                'hora_salida': asistencia.hora_salida.strftime('%H:%M:%S') if asistencia.hora_salida else None,
                'horas_extras': float(asistencia.horas_extras),
                'horas_faltantes': float(asistencia.horas_faltantes),
                'estado': asistencia.estado
            })
            
            reporte_por_empleado[empleado_id]['total_horas_extras'] += asistencia.horas_extras
            reporte_por_empleado[empleado_id]['total_horas_faltantes'] += asistencia.horas_faltantes
            
            if asistencia.estado == Asistencia.Estado.COMPLETO:
                reporte_por_empleado[empleado_id]['dias_completos'] += 1
            elif asistencia.estado == Asistencia.Estado.INCOMPLETO:
                reporte_por_empleado[empleado_id]['dias_incompletos'] += 1
            elif asistencia.estado == Asistencia.Estado.EXTRA:
                reporte_por_empleado[empleado_id]['dias_extras'] += 1
        
        # Convertir a lista y formatear decimales
        reporte = []
        for datos in reporte_por_empleado.values():
            datos['total_horas_extras'] = float(datos['total_horas_extras'])
            datos['total_horas_faltantes'] = float(datos['total_horas_faltantes'])
            dias_asistidos = datos['dias_completos'] + datos['dias_incompletos'] + datos['dias_extras']
            datos['dias_asistidos'] = dias_asistidos
            datos['dias_habiles_mes'] = dias_habiles_mes
            datos['dias_faltantes_mes'] = max(dias_habiles_mes - dias_asistidos, 0)
            reporte.append(datos)
        
        return Response({
            'año': año,
            'mes': mes,
            'dias_habiles_mes': dias_habiles_mes,
            'reporte': reporte
        }, status=status.HTTP_200_OK)


# ============================================
# VISTA SIMPLE PARA MARCAR ASISTENCIA
# APIView de DRF - NO REQUIERE CSRF
# ============================================