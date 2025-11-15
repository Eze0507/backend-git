from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import requests
from operaciones_inventario.modelsItem import Item
from operaciones_inventario.serializers.serializerItem import ItemSerializer
from personal_admin.views import registrar_bitacora
from personal_admin.models import Bitacora

class ItemViewSet(viewsets.ModelViewSet):
    
    serializer_class = ItemSerializer
    
    def get_queryset(self):
        user_tenant = self.request.user.profile.tenant
        return Item.objects.filter(tenant=user_tenant)

    def create(self, request, *args, **kwargs):
        return self.handle_image_upload(request, is_update=False)

    def update(self, request, *args, **kwargs):
        return self.handle_image_upload(request, is_update=True, *args, **kwargs)

    def handle_image_upload(self, request, is_update=False, *args, **kwargs):
        # Crear una copia mutable de los datos
        data = request.data.copy()
        imagen_file = request.FILES.get("imagen")

        if imagen_file:
            # Subir imagen a ImgBB
            url = "https://api.imgbb.com/1/upload"
            payload = {"key": settings.API_KEY_IMGBB}
            files = {"image": imagen_file.read()}
            
            try:
                response = requests.post(url, data=payload, files=files)
                response.raise_for_status()  # Lanza excepción si hay error HTTP
                
                if response.status_code == 200:
                    image_url = response.json()["data"]["url"]
                    data["imagen"] = image_url
                else:
                    return Response(
                        {"error": "Error al subir imagen a ImgBB"}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            except requests.exceptions.RequestException as e:
                return Response(
                    {"error": f"Error de conexión con ImgBB: {str(e)}"}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        elif is_update:
            # Si es una actualización y no hay nueva imagen, mantener la existente
            instance = self.get_object()
            if not data.get("imagen") and instance.imagen:
                data["imagen"] = instance.imagen

        # Crear el serializer con los datos procesados
        if is_update:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=data, partial=kwargs.get('partial', False))
        else:
            serializer = self.get_serializer(data=data)

        if serializer.is_valid():
            
            user_tenant = request.user.profile.tenant
            instance = serializer.save(tenant=user_tenant)
            
            # Registrar en bitácora
            if is_update:
                descripcion = f"Item '{instance.nombre}' actualizado con código '{instance.codigo}'"
                accion = Bitacora.Accion.EDITAR
            else:
                descripcion = f"Item '{instance.nombre}' creado con código '{instance.codigo}'"
                accion = Bitacora.Accion.CREAR
            
            registrar_bitacora(
                usuario=request.user,
                accion=accion,
                modulo=Bitacora.Modulo.ITEM,
                descripcion=descripcion,
                request=request
            )
            
            return Response(serializer.data, status=status.HTTP_201_CREATED if not is_update else status.HTTP_200_OK)
        else:
            return Response(
                {"error": "Datos inválidos", "details": serializer.errors}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Registrar en bitácora antes de eliminar
        descripcion = f"Item '{instance.nombre}' eliminado con código '{instance.codigo}'"
        registrar_bitacora(
            usuario=request.user,
            accion=Bitacora.Accion.ELIMINAR,
            modulo=Bitacora.Modulo.ITEM,
            descripcion=descripcion,
            request=request
        )
        
        # Llamar al método destroy del padre
        return super().destroy(request, *args, **kwargs)
