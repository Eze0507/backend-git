from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, IntegerField
from .models import Cliente
from .serializers.serializer_cliente import ClienteSerializer


class ClienteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar Clientes.
    - Listar con filtros y búsqueda
    - Borrado lógico
    """
    queryset = Cliente.objects.filter(activo=True).order_by('nombre', 'apellido')
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]


    def destroy(self, request, *args, **kwargs):
        """Borrado lógico en lugar de delete físico"""
        instance = self.get_object()
        instance.activo = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


