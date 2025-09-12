from django.shortcuts import render
from rest_framework import viewsets, status
from .serializers.serializers_user import UserSerializer, GroupAuxSerializer
from .serializers.serializers_register import UserRegistrationSerializer
from django.contrib.auth.models import User, Group
from .models import Cargo
from .serializers.serializers_cargo import CargoSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

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