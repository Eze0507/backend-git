# clientes_servicios/views.py
from django.shortcuts import get_object_or_404
from django.db.models import Q, IntegerField
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import Cliente
#from .serializers_cliente import ClienteSerializer
from .serializers.serializer_cliente import ClienteSerializer


# Listar (GET) y Crear (POST)
@api_view(['GET', 'POST'])
def cliente_list(request):
    if request.method == 'GET':
        q = request.GET.get('q', '').strip()
        tipo = request.GET.get('tipo', '').strip()
        qs = Cliente.objects.filter(activo=True)

        if q:
            filtros = (
                Q(nombre__icontains=q) |
                Q(apellido__icontains=q) |
                Q(telefono__icontains=q) |
                Q(correo__icontains=q)
            )
            try:
                nit_field = Cliente._meta.get_field('nit')
                if isinstance(nit_field, IntegerField):
                    if q.isdigit():
                        filtros = filtros | Q(nit=int(q))
                else:
                    filtros = filtros | Q(nit__icontains=q)
            except Exception:
                pass
            qs = qs.filter(filtros)

        if tipo:
            qs = qs.filter(tipo_cliente__iexact=tipo)

        qs = qs.order_by('nombre', 'apellido')

        # paginación simple
        page_size = 10
        page_number = request.GET.get('page', 1)
        paginator = Paginator(qs, page_size)
        try:
            page_obj = paginator.page(page_number)
        except (PageNotAnInteger, EmptyPage):
            page_obj = paginator.page(1)

        serializer = ClienteSerializer(page_obj.object_list, many=True)
        return Response({
            'count': paginator.count,
            'num_pages': paginator.num_pages,
            'page': page_obj.number,
            'results': serializer.data
        }, status=status.HTTP_200_OK)

    # POST -> crear
    serializer = ClienteSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Detalle (GET), Actualizar (PUT) y Borrado lógico (DELETE)
@api_view(['GET', 'PUT', 'DELETE'])
def cliente_detail(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)

    if request.method == 'GET':
        serializer = ClienteSerializer(cliente)
        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.method == 'PUT':
        serializer = ClienteSerializer(cliente, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # DELETE -> borrado lógico
    cliente.activo = False
    cliente.save()
    return Response(status=status.HTTP_204_NO_CONTENT)
