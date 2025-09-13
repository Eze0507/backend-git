from django.shortcuts import render
from rest_framework import viewsets, status,filters, permissions,generics
from .serializers.serializers_user import UserSerializer, GroupAuxSerializer
from django.db.models import ProtectedError
from .serializers.serializers_register import UserRegistrationSerializer
from django.contrib.auth.models import User, Group
from .models import Cargo
from .serializers.serializers_cargo import CargoSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers.serializers_rol import RoleSerializer 
from rest_framework.permissions import IsAuthenticated, AllowAny 
from personal_admin.models import Empleado
from .serializers.serializers_empleado import EmpleadoReadSerializer, EmpleadoWriteSerializer
from clientes_servicios.models import Cliente
from personal_admin.serializers.serializers_profile import ProfileUpdateSerializer, EmpleadoProfileUpdateSerializer
from rest_framework import permissions
from rest_framework import status
from .serializers.serializers_password import ChangePasswordSerializer
from rest_framework.exceptions import NotFound
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie


# ---- ViewSets de tus compañeros ----
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

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


# ---- Tu nuevo ViewSet para Roles ----
class RoleViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all().order_by('name')
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]


#viewset para actualizar perfil cliente y empleado
class ClienteProfileUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Cliente.objects.all()
    serializer_class = ProfileUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        try:
            return Cliente.objects.get(usuario=self.request.user)
        except Cliente.DoesNotExist:
            raise NotFound("No existe perfil de cliente para este usuario.")

class EmpleadoProfileUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = EmpleadoProfileUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        try:
            return Empleado.objects.get(usuario=self.request.user)
        except Empleado.DoesNotExist:
            raise NotFound("No existe perfil de empleado para este usuario.")

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
class IsStaffOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_staff

class EmpleadoViewSet(viewsets.ModelViewSet):
    queryset = Empleado.objects.select_related("cargo", "usuario").all()
    permission_classes = [IsStaffOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]  # puedes añadir DjangoFilterBackend si lo instalas
    search_fields = ["nombre", "apellido", "ci", "telefono"]
    ordering_fields = ["apellido", "nombre", "ci", "fecha_registro", "sueldo"]
    ordering = ["apellido", "nombre"]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return EmpleadoWriteSerializer
        return EmpleadoReadSerializer

@method_decorator(csrf_exempt, name='dispatch')
class CustomTokenObtainPairView(TokenObtainPairView):
    pass

@method_decorator(ensure_csrf_cookie, name='dispatch')
class CSRFTokenView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({ "detail": "CSRF cookie set" })
