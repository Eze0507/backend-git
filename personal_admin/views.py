from django.shortcuts import render
from rest_framework import viewsets, status,filters, permissions,generics
from .serializers.serializers_user import UserSerializer, GroupAuxSerializer
from django.db.models import ProtectedError
from .serializers.serializers_register import UserRegistrationSerializer
from django.contrib.auth.models import User, Group, Permission
from .models import Cargo, Bitacora
from .serializers.serializers_cargo import CargoSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.views import TokenObtainPairView
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


# ---- ViewSets de tus compañeros ----
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def perform_create(self, serializer):
        """Crear usuario y registrar en bitácora"""
        # Ejecutar la creación original
        instance = serializer.save()
        
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
    queryset = Cargo.objects.all()
    serializer_class = CargoSerializer


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
    queryset = Empleado.objects.select_related("cargo", "usuario").all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]  
    search_fields = ["nombre", "apellido", "ci", "telefono"]
    ordering_fields = ["apellido", "nombre", "ci", "fecha_registro", "sueldo"]
    ordering = ["apellido", "nombre"]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return EmpleadoWriteSerializer
        return EmpleadoReadSerializer
    
    def perform_create(self, serializer):
        """Crear empleado y registrar en bitácora"""
        # Ejecutar la creación original
        instance = serializer.save()
        
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
        
        Bitacora.objects.create(
            usuario=usuario,
            accion=accion,
            modulo=modulo,
            descripcion=descripcion,
            ip_address=ip_address
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
    queryset = Bitacora.objects.select_related('usuario').all()
    serializer_class = BitacoraSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['descripcion', 'usuario__username', 'usuario__email', 'ip_address']
    ordering_fields = ['fecha_accion', 'usuario__username', 'modulo', 'accion']
    ordering = ['-fecha_accion']  # Más recientes primero
    
    def get_queryset(self):
        """Filtros personalizados para la bitácora"""
        queryset = super().get_queryset()
        
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
