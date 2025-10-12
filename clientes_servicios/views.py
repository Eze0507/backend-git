from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, IntegerField
from .models import Cliente
from .serializers.serializer_cliente import ClienteSerializer
from personal_admin.views import registrar_bitacora
from personal_admin.models import Bitacora


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


