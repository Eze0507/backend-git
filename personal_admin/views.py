from django.shortcuts import render
from rest_framework import viewsets, status, filters, permissions
from .serializers.serializers_user import UserSerializer, GroupAuxSerializer
from .serializers.serializers_register import UserRegistrationSerializer
from django.contrib.auth.models import User, Group
from .models import Cargo
from .serializers.serializers_user import UserSerializer, GroupAuxSerializer
from .serializers.serializers_cargo import CargoSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from .serializers.serializers_rol import RoleSerializer 
from rest_framework.permissions import IsAuthenticated 
from personal_admin.models import Empleado
from .serializers.serializers_empleado import EmpleadoReadSerializer, EmpleadoWriteSerializer


# ---- ViewSets de tus compañeros ----
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class GroupAuxViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupAuxSerializer


class UserRegistrationView(APIView):
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
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
