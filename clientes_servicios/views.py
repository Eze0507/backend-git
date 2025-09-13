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

    def list(self, request, *args, **kwargs):
        """Listar clientes con filtros y búsqueda"""
        q = request.GET.get('q', '').strip()
        tipo = request.GET.get('tipo', '').strip()
        qs = self.queryset

        if q:
            filtros = (
                Q(nombre__icontains=q) |
                Q(apellido__icontains=q) |
                Q(telefono__icontains=q) |
                Q(usuario__email__icontains=q)  # <-- buscar en email del usuario
            )
            try:
                nit_field = Cliente._meta.get_field('nit')
                if hasattr(nit_field, 'get_internal_type') and nit_field.get_internal_type() == 'IntegerField':
                    if q.isdigit():
                        filtros |= Q(nit=int(q))
                else:
                    filtros |= Q(nit__icontains=q)
            except Exception:
                pass
            qs = qs.filter(filtros)

        if tipo:
            qs = qs.filter(tipo_cliente__iexact=tipo)

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """Borrado lógico en lugar de delete físico"""
        instance = self.get_object()
        instance.activo = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


