import requests
from rest_framework import mixins, viewsets
from rest_framework.response import Response
from django.conf import settings
from .modelsOrdenTrabajo import OrdenTrabajo, DetalleOrdenTrabajo, NotaOrdenTrabajo, TareaOrdenTrabajo, InventarioVehiculo, Inspeccion, PruebaRuta, AsignacionTecnico, ImagenOrdenTrabajo
from .serializers.serializersOrdenTrabajo import (OrdenTrabajoSerializer, DetalleOrdenTrabajoSerializer, 
OrdenTrabajoCreateSerializer, NotaOrdenTrabajoSerializer, TareaOrdenTrabajoSerializer, inventarioVehiculoSerializer, 
inspeccionSerializer, PruebaRutaSerializer, AsignacionTecnicoSerializer, ImagenOrdenTrabajoSerializer)
from personal_admin.views import registrar_bitacora
from personal_admin.models import Bitacora


class OrdenTrabajoViewSet(viewsets.ModelViewSet):
    queryset = OrdenTrabajo.objects.all()
    
    def get_serializer_class(self):
        """Usar diferentes serializers según la acción"""
        if self.action == 'create':
            return OrdenTrabajoCreateSerializer  
        return OrdenTrabajoSerializer         
    
    def get_queryset(self):
        """Optimizar consultas con select_related y prefetch_related"""
        return OrdenTrabajo.objects.select_related(
            'cliente', 'vehiculo'
        ).prefetch_related('detalles', 'detalles__item', 'notas', 'tareas', 'inventario_vehiculo', 'inspecciones', 'pruebas_ruta', 'asignaciones_tecnicos', 'imagenes')
    
    def perform_create(self, serializer):
        # Primero, crea el objeto para tener su ID
        orden = serializer.save()
        
        # Luego, registra la acción en la bitácora
        registrar_bitacora(
            usuario=self.request.user,
            accion=Bitacora.Accion.CREAR,
            modulo=Bitacora.Modulo.ORDEN_TRABAJO,
            descripcion=f"Se creó la orden de trabajo #{orden.id} para el cliente '{orden.cliente.nombre}'.",
            request=self.request
        )

    def perform_update(self, serializer):
        orden = serializer.save()
        registrar_bitacora(
            usuario=self.request.user,
            accion=Bitacora.Accion.EDITAR,
            modulo=Bitacora.Modulo.ORDEN_TRABAJO,
            descripcion=f"Se actualizó la orden de trabajo #{orden.id}.",
            request=self.request
        )

    def perform_destroy(self, instance):
        # Obtenemos la información ANTES de borrar el objeto
        descripcion = f"Se eliminó la orden de trabajo #{instance.id} del cliente '{instance.cliente.nombre}'."
        
        # Eliminamos el objeto
        instance.delete()
        
        # Registramos la acción
        registrar_bitacora(
            usuario=self.request.user,
            accion=Bitacora.Accion.ELIMINAR,
            modulo=Bitacora.Modulo.ORDEN_TRABAJO,
            descripcion=descripcion,
            request=self.request
        )

class DetalleOrdenTrabajoViewSet(viewsets.ModelViewSet):
    serializer_class = DetalleOrdenTrabajoSerializer
    
    def get_queryset(self):
        """Filtrar por orden si se pasa el parámetro"""
        if 'orden_pk' in self.kwargs:
            return DetalleOrdenTrabajo.objects.filter(
                orden_trabajo_id=self.kwargs['orden_pk']
            ).select_related('item', 'orden_trabajo')
        return DetalleOrdenTrabajo.objects.all()

    def perform_create(self, serializer):
        """Asignar la orden automáticamente y registrar en bitácora"""
        orden = None
        if 'orden_pk' in self.kwargs:
            orden = OrdenTrabajo.objects.get(pk=self.kwargs['orden_pk'])
            detalle = serializer.save(orden_trabajo=orden)
        else:
            detalle = serializer.save()
        # Registrar en la bitácora
        registrar_bitacora(
            usuario=self.request.user,
            accion=Bitacora.Accion.CREAR,
            modulo=Bitacora.Modulo.ORDEN_TRABAJO,
            descripcion=f"Se añadió el detalle '{detalle.nombre_item}' a la orden de trabajo #{detalle.orden_trabajo.id}.",
            request=self.request
        )

    def perform_destroy(self, instance):
        """Eliminar el detalle y registrar en bitácora"""
        # Obtenemos la información ANTES de borrar el objeto
        descripcion = f"Se eliminó el detalle '{instance.nombre_item}' de la orden de trabajo #{instance.orden_trabajo.id}."
        
        # Eliminamos el objeto
        instance.delete()
        
        # Registramos la acción
        registrar_bitacora(
            usuario=self.request.user,
            accion=Bitacora.Accion.ELIMINAR,
            modulo=Bitacora.Modulo.ORDEN_TRABAJO,
            descripcion=descripcion,
            request=self.request
        )

class NotaOrdenTrabajoViewSet(viewsets.ModelViewSet):
    serializer_class = NotaOrdenTrabajoSerializer
    
    def get_queryset(self):
        """Devuelve SÓLO las notas que pertenecen a la orden de la URL.
        Si 'orden_pk' no está, la petición fallará, lo cual es correcto."""
        return NotaOrdenTrabajo.objects.filter(
            orden_trabajo_id=self.kwargs['orden_pk']
        )

    def perform_create(self, serializer):
        """Asocia la nueva nota con la orden de la URL."""
        orden = OrdenTrabajo.objects.get(pk=self.kwargs['orden_pk'])
        serializer.save(orden_trabajo=orden)
    
    def perform_create(self, serializer):
        # La lógica de asociar la orden ya está aquí, la reutilizamos
        orden = OrdenTrabajo.objects.get(pk=self.kwargs['orden_pk'])
        nota = serializer.save(orden_trabajo=orden)
        
        registrar_bitacora(
            usuario=self.request.user,
            accion=Bitacora.Accion.CREAR,
            modulo=Bitacora.Modulo.ORDEN_TRABAJO,
            descripcion=f"Se añadió una nota a la orden de trabajo #{orden.id}.",
            request=self.request
        )

    def perform_destroy(self, instance):
        orden_id = instance.orden_trabajo.id
        descripcion = f"Se eliminó una nota de la orden de trabajo #{orden_id}."
        
        instance.delete()
        
        registrar_bitacora(
            usuario=self.request.user,
            accion=Bitacora.Accion.ELIMINAR,
            modulo=Bitacora.Modulo.ORDEN_TRABAJO,
            descripcion=descripcion,
            request=self.request
        )

class TareaOrdenTrabajoViewSet(viewsets.ModelViewSet):
    serializer_class = TareaOrdenTrabajoSerializer

    def get_queryset(self):
        """Devuelve SÓLO las tareas que pertenecen a la orden de la URL.
        Si 'orden_pk' no está, la petición fallará, lo cual es correcto."""
        return TareaOrdenTrabajo.objects.filter(
            orden_trabajo_id=self.kwargs['orden_pk']
        )

    def perform_create(self, serializer):
        """Asocia la nueva tarea con la orden y registra en bitácora."""
        orden = OrdenTrabajo.objects.get(pk=self.kwargs['orden_pk'])
        tarea = serializer.save(orden_trabajo=orden)

        # Registrar en la bitácora
        registrar_bitacora(
            usuario=self.request.user,
            accion=Bitacora.Accion.CREAR,
            modulo=Bitacora.Modulo.ORDEN_TRABAJO,
            descripcion=f"Se añadió la tarea '{tarea.descripcion}' a la orden de trabajo #{orden.id}.",
            request=self.request
        )

    def perform_update(self, serializer):
        """Actualiza la tarea y registra en bitácora."""
        tarea = serializer.save()
        
        # Decide el mensaje basado en si la tarea se completó o no
        if 'completada' in serializer.validated_data:
            estado = "marcó como completada" if tarea.completada else "marcó como pendiente"
            descripcion = f"Se {estado} la tarea '{tarea.descripcion}' en la orden #{tarea.orden_trabajo.id}."
        else:
            descripcion = f"Se actualizó la tarea '{tarea.descripcion}' en la orden #{tarea.orden_trabajo.id}."

        registrar_bitacora(
            usuario=self.request.user,
            accion=Bitacora.Accion.EDITAR,
            modulo=Bitacora.Modulo.ORDEN_TRABAJO,
            descripcion=descripcion,
            request=self.request
        )

    def perform_destroy(self, instance):
        """Elimina la tarea y registra en bitácora."""
        # Obtenemos la información ANTES de borrar el objeto
        descripcion = f"Se eliminó la tarea '{instance.descripcion}' de la orden de trabajo #{instance.orden_trabajo.id}."
        
        # Eliminamos el objeto
        instance.delete()
        
        # Registramos la acción
        registrar_bitacora(
            usuario=self.request.user,
            accion=Bitacora.Accion.ELIMINAR,
            modulo=Bitacora.Modulo.ORDEN_TRABAJO,
            descripcion=descripcion,
            request=self.request
        )

class inventarioVehiculoViewSet(mixins.CreateModelMixin,
                                mixins.UpdateModelMixin, 
                                viewsets.GenericViewSet):
    serializer_class = inventarioVehiculoSerializer

    def get_queryset(self):
        """Devuelve SÓLO los inventarios que pertenecen a la orden de la URL.
        Si 'orden_pk' no está, la petición fallará, lo cual es correcto."""
        return InventarioVehiculo.objects.filter(
            orden_trabajo_id=self.kwargs['orden_pk']
        )

    def perform_create(self, serializer):
        """Asocia el nuevo inventario con la orden de la URL."""
        orden = OrdenTrabajo.objects.get(pk=self.kwargs['orden_pk'])
        serializer.save(orden_trabajo=orden)
    
    def perform_update(self, serializer):
        """Actualiza el inventario y registra la acción en la bitácora."""
        inventario = serializer.save()

        registrar_bitacora(
            usuario=self.request.user,
            accion=Bitacora.Accion.EDITAR,
            modulo=Bitacora.Modulo.ORDEN_TRABAJO,
            descripcion=f"Se actualizó el inventario de vehículo de la orden de trabajo #{inventario.orden_trabajo.id}.",
            request=self.request
        )

class inspeccionViewSet(viewsets.ModelViewSet):
    serializer_class = inspeccionSerializer

    def get_queryset(self):
        """Devuelve SÓLO las inspecciones que pertenecen a la orden de la URL.
        Si 'orden_pk' no está, la petición fallará, lo cual es correcto."""
        return Inspeccion.objects.filter(
            orden_trabajo_id=self.kwargs['orden_pk']
        ).select_related('tecnico')

    def perform_create(self, serializer):
        """Asocia la nueva inspección con la orden y registra en bitácora."""
        orden = OrdenTrabajo.objects.get(pk=self.kwargs['orden_pk'])
        inspeccion = serializer.save(orden_trabajo=orden)

        # Registrar en la bitácora
        registrar_bitacora(
            usuario=self.request.user,
            accion=Bitacora.Accion.CREAR,
            modulo=Bitacora.Modulo.ORDEN_TRABAJO,
            descripcion=f"Se añadió una inspección de '{inspeccion.get_tipo_inspeccion_display()}' a la orden de trabajo #{orden.id}.",
            request=self.request
        )

    def perform_update(self, serializer):
        """Actualiza la inspección y registra en bitácora."""
        inspeccion = serializer.save()

        registrar_bitacora(
            usuario=self.request.user,
            accion=Bitacora.Accion.EDITAR,
            modulo=Bitacora.Modulo.ORDEN_TRABAJO,
            descripcion=f"Se actualizó la inspección de '{inspeccion.get_tipo_inspeccion_display()}' en la orden de trabajo #{inspeccion.orden_trabajo.id}.",
            request=self.request
        )

    def perform_destroy(self, instance):
        """Elimina la inspección y registra en bitácora."""
        # Obtenemos la información ANTES de borrar el objeto
        descripcion = f"Se eliminó la inspección de '{instance.get_tipo_inspeccion_display()}' de la orden de trabajo #{instance.orden_trabajo.id}."
        
        # Eliminamos el objeto
        instance.delete()
        
        # Registramos la acción
        registrar_bitacora(
            usuario=self.request.user,
            accion=Bitacora.Accion.ELIMINAR,
            modulo=Bitacora.Modulo.ORDEN_TRABAJO,
            descripcion=descripcion,
            request=self.request
        )

class PruebaRutaViewSet(viewsets.ModelViewSet):
    serializer_class = PruebaRutaSerializer

    def get_queryset(self):
        """Devuelve SÓLO las pruebas de ruta que pertenecen a la orden de la URL."""
        return PruebaRuta.objects.filter(
            orden_trabajo_id=self.kwargs['orden_pk']
        ).select_related('tecnico')
        
    def perform_create(self, serializer):
        """Asocia la nueva prueba de ruta con la orden y registra en bitácora."""
        orden = OrdenTrabajo.objects.get(pk=self.kwargs['orden_pk'])
        prueba = serializer.save(orden_trabajo=orden)

        # Registrar en la bitácora
        registrar_bitacora(
            usuario=self.request.user,
            accion=Bitacora.Accion.CREAR,
            modulo=Bitacora.Modulo.ORDEN_TRABAJO,
            descripcion=f"Se añadió una prueba de ruta de tipo '{prueba.get_tipo_prueba_display()}' a la orden de trabajo #{orden.id}.",
            request=self.request
        )

    def perform_update(self, serializer):
        """Actualiza la prueba de ruta y registra en bitácora."""
        prueba = serializer.save()

        registrar_bitacora(
            usuario=self.request.user,
            accion=Bitacora.Accion.EDITAR,
            modulo=Bitacora.Modulo.ORDEN_TRABAJO,
            descripcion=f"Se actualizó la prueba de ruta de tipo '{prueba.get_tipo_prueba_display()}' en la orden de trabajo #{prueba.orden_trabajo.id}.",
            request=self.request
        )

    def perform_destroy(self, instance):
        """Elimina la prueba de ruta y registra en bitácora."""
        # Obtenemos la información ANTES de borrar el objeto
        descripcion = f"Se eliminó la prueba de ruta de tipo '{instance.get_tipo_prueba_display()}' de la orden de trabajo #{instance.orden_trabajo.id}."
        
        # Eliminamos el objeto
        instance.delete()
        
        # Registramos la acción
        registrar_bitacora(
            usuario=self.request.user,
            accion=Bitacora.Accion.ELIMINAR,
            modulo=Bitacora.Modulo.ORDEN_TRABAJO,
            descripcion=descripcion,
            request=self.request
        )

class AsignacionTecnicoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para asignar, ver y eliminar técnicos de una orden de trabajo.
    """
    serializer_class = AsignacionTecnicoSerializer

    def get_queryset(self):
        """
        Filtra las asignaciones para devolver solo las de la orden de la URL.
        """
        return AsignacionTecnico.objects.filter(
            orden_trabajo_id=self.kwargs['orden_pk']
        ).select_related('tecnico') # Optimización para cargar datos del técnico

    def perform_create(self, serializer):
        orden = OrdenTrabajo.objects.get(pk=self.kwargs['orden_pk'])
        asignacion = serializer.save(orden_trabajo=orden)

        nombre_tecnico = "N/A"
        if asignacion.tecnico:
            # --- CORRECCIÓN AQUÍ ---
            # Usamos '.nombre' en lugar de '.get_full_name()'
            nombre_tecnico = asignacion.tecnico.nombre or asignacion.tecnico.username

        registrar_bitacora(
            usuario=self.request.user,
            accion=Bitacora.Accion.CREAR,
            modulo=Bitacora.Modulo.ORDEN_TRABAJO,
            descripcion=f"Se asignó al técnico '{nombre_tecnico}' a la orden de trabajo #{orden.id}.",
            request=self.request
        )

    def perform_destroy(self, instance):
        nombre_tecnico = "N/A"
        if instance.tecnico:
            # --- CORRECCIÓN AQUÍ ---
            # Usamos '.nombre' en lugar de '.get_full_name()'
            nombre_tecnico = instance.tecnico.nombre or instance.tecnico.username
        
        descripcion = f"Se eliminó la asignación del técnico '{nombre_tecnico}' de la orden de trabajo #{instance.orden_trabajo.id}."
        
        instance.delete()
        
        registrar_bitacora(
            usuario=self.request.user,
            accion=Bitacora.Accion.ELIMINAR,
            modulo=Bitacora.Modulo.ORDEN_TRABAJO,
            descripcion=descripcion,
            request=self.request
        )

class ImagenOrdenTrabajoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para manejar las imágenes de una orden de trabajo,
    incluyendo la subida de archivos a ImgBB.
    """
    serializer_class = ImagenOrdenTrabajoSerializer

    def get_queryset(self):
        return ImagenOrdenTrabajo.objects.filter(
            orden_trabajo_id=self.kwargs['orden_pk']
        )

    def perform_create(self, serializer):
        """Asocia la nueva imagen con la orden y registra en bitácora."""
        orden = OrdenTrabajo.objects.get(pk=self.kwargs['orden_pk'])
        # Guardamos la imagen primero para obtener la instancia
        imagen = serializer.save(orden_trabajo=orden)

        registrar_bitacora(
            usuario=self.request.user,
            accion=Bitacora.Accion.CREAR,
            modulo=Bitacora.Modulo.ORDEN_TRABAJO,
            descripcion=f"Se añadió una imagen a la orden de trabajo #{orden.id}.",
            request=self.request
        )

    def perform_destroy(self, instance):
        """Elimina la imagen y registra en bitácora."""
        descripcion = f"Se eliminó una imagen de la orden de trabajo #{instance.orden_trabajo.id}."
        
        instance.delete()
        
        registrar_bitacora(
            usuario=self.request.user,
            accion=Bitacora.Accion.ELIMINAR,
            modulo=Bitacora.Modulo.ORDEN_TRABAJO,
            descripcion=descripcion,
            request=self.request
        )

    # --- LÓGICA DE SUBIDA DE IMAGEN ADAPTADA ---

    def create(self, request, *args, **kwargs):
        return self.handle_image_upload(request, super().create)

    def update(self, request, *args, **kwargs):
        # Usamos 'partial=True' para que PATCH también funcione correctamente
        partial = kwargs.pop('partial', False)
        # La acción a ejecutar es la actualización del objeto padre
        action = lambda req, *a, **kw: super().update(req, partial=partial, *a, **kw)
        return self.handle_image_upload(request, action, *args, **kwargs)

    def handle_image_upload(self, request, action, *args, **kwargs):
        # El frontend enviará el archivo bajo la clave 'imagen_file'
        imagen_file = request.FILES.get("imagen_file")
        data = request.data.copy()

        if imagen_file:
            url = "https://api.imgbb.com/1/upload"
            payload = {"key": settings.API_KEY_IMGBB}
            files = {"image": imagen_file.read()}
            response = requests.post(url, payload, files=files)

            if response.status_code == 200:
                image_url = response.json()["data"]["url"]
                # Modificamos el campo 'imagen_url' con la URL obtenida
                data["imagen_url"] = image_url
            else:
                return Response({"error": "Error al subir la imagen a ImgBB"}, status=500)
        
        # Pasamos los datos modificados (o los originales si no hay archivo) a la acción
        # Esto reemplaza el método de modificar request._full_data que es menos estándar
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        # Ejecutamos la acción original (create o update) pero con el serializer que ya tiene la URL
        if self.request.method in ['PUT', 'PATCH']:
            instance = self.get_object()
            serializer.instance = instance
            self.perform_update(serializer)
        else: # POST
            self.perform_create(serializer)
            
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=201 if self.request.method == 'POST' else 200, headers=headers)
