import time, requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from .models import LecturaPlaca
from .serializers.serializersPlaca import LecturaPlacaSerializer
from operaciones_inventario.modelsVehiculos import Vehiculo
from personal_admin.views import registrar_bitacora
from personal_admin.models import Bitacora


PLATE_URL = "https://api.platerecognizer.com/v1/plate-reader/"

class AlprScanView(APIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request, *args, **kwargs):
        token = settings.PLATE_TOKEN
        if not token:
            return Response({"error": "Configura PLATE_TOKEN"}, status=500)

        # Aceptar: archivo multipart o base64
        user_tenant = request.user.profile.tenant
        f = request.FILES.get("upload") or request.FILES.get("image")
        image_base64 = request.data.get("image_base64")
        
        if not f and not image_base64:
            return Response({
                "error": "Debes enviar el archivo en 'upload', 'image' o 'image_base64'."
            }, status=400)
        
        # Si viene base64, convertir a archivo en memoria
        if image_base64:
            import base64
            from io import BytesIO
            from django.core.files.uploadedfile import InMemoryUploadedFile
            
            try:
                # Remover el prefijo data:image/...;base64, si existe
                if ',' in image_base64:
                    image_base64 = image_base64.split(',')[1]
                
                image_data = base64.b64decode(image_base64)
                image_file = BytesIO(image_data)
                
                f = InMemoryUploadedFile(
                    image_file,
                    None,
                    'image.jpg',
                    'image/jpeg',
                    len(image_data),
                    None
                )
            except Exception as e:
                return Response({
                    "error": "Error al decodificar imagen base64",
                    "detail": str(e)
                }, status=400)
        
        if f and not getattr(f, "content_type", "").startswith("image/"):
            return Response({"error": "El archivo debe ser una imagen."}, status=400)

        camera_id = request.data.get("camera_id", "") or ""
        regions   = request.data.get("regions") or settings.PLATE_REGIONS

        headers = {"Authorization": f"Token {token}"}
        payload = {"regions": regions}
        if camera_id:
            payload["camera_id"] = camera_id

        files = {"upload": (getattr(f, "name", "frame.jpg"), f, getattr(f, "content_type", "image/jpeg"))}
        try:
            f.seek(0)
            r = requests.post(PLATE_URL, headers=headers, data=payload, files=files, timeout=20)
            if r.status_code == 429:
                time.sleep(1)
                f.seek(0)
                r = requests.post(PLATE_URL, headers=headers, data=payload, files=files, timeout=20)
        except requests.RequestException as e:
            return Response({"error": "No se pudo contactar al ALPR", "detail": str(e)}, status=502)

        # 🔧 ACEPTAR 200/201 COMO ÉXITO
        if r.status_code not in (200, 201):
            return Response({"error": "ALPR no respondió OK", "status_code": r.status_code, "detail": r.text}, status=r.status_code)

        js = r.json()
        results = js.get("results", [])

        if not results:
            l = LecturaPlaca.objects.create(placa="", score=0.0, camera_id=camera_id, vehiculo=None, match=False, tenant=user_tenant)
            
            # Registrar en bitácora: No se detectó placa
            registrar_bitacora(
                usuario=request.user,
                accion=Bitacora.Accion.CONSULTAR,
                modulo=Bitacora.Modulo.RECONOCIMIENTO_PLACAS,
                descripcion=f"Reconocimiento de placa sin resultado. No se detectó ninguna placa en la imagen (cámara: {camera_id})",
                request=request
            )
            
            return Response({
                "status": "no-plate-found",
                "plate": None, "score": None, "match": False,
                "vehiculo": None,
                "lectura": LecturaPlacaSerializer(l).data
            }, status=200)

        best      = max(results, key=lambda x: x.get("score", 0) or 0.0)
        plate_raw = (best.get("plate") or "").upper()
        score     = float(best.get("score") or 0.0)

        v_match = (Vehiculo.objects.filter(tenant=user_tenant, numero_placa__iexact=plate_raw)   # BD ya normalizada
                .select_related("cliente")
                .first())

        lectura = LecturaPlaca.objects.create(
            placa=plate_raw, score=score, camera_id=camera_id,
            vehiculo=v_match, match=bool(v_match),
            tenant=user_tenant
        )

        from operaciones_inventario.serializers.serializersVehiculo import VehiculoDetailSerializer
        
        # Obtener órdenes pendientes del vehículo si hay match
        ordenes_pendientes = []
        if v_match:
            from operaciones_inventario.modelsOrdenTrabajo import OrdenTrabajo
            ordenes = OrdenTrabajo.objects.filter(
                vehiculo=v_match,
                estado__in=['pendiente', 'en_proceso']
            ).order_by('-fecha_creacion')
            
            # Usar el cliente del vehículo, NO el cliente de la orden
            ordenes_pendientes = [{
                'id': orden.id,
                'estado': orden.estado,
                'fecha_creacion': orden.fecha_creacion,
                'fallo_requerimiento': orden.fallo_requerimiento,
                'total': float(orden.total),
                'cliente': {
                    'id': v_match.cliente.id if v_match.cliente else None,
                    'nombre': v_match.cliente.nombre if v_match.cliente else None,
                    'apellido': v_match.cliente.apellido if v_match.cliente else None,
                }
            } for orden in ordenes]
            
            # Registrar en bitácora: Vehículo ENCONTRADO
            cliente_nombre = f"{v_match.cliente.nombre} {v_match.cliente.apellido}" if v_match.cliente else "Sin cliente"
            marca_modelo = f"{v_match.marca.nombre if v_match.marca else 'N/A'} {v_match.modelo.nombre if v_match.modelo else 'N/A'}"
            ordenes_info = f"{len(ordenes_pendientes)} orden(es) pendiente(s)" if ordenes_pendientes else "sin órdenes pendientes"
            
            registrar_bitacora(
                usuario=request.user,
                accion=Bitacora.Accion.CONSULTAR,
                modulo=Bitacora.Modulo.RECONOCIMIENTO_PLACAS,
                descripcion=f"Placa '{plate_raw}' reconocida con éxito (confianza: {score*100:.1f}%). Vehículo: {marca_modelo}, Cliente: {cliente_nombre}, {ordenes_info}",
                request=request
            )
        else:
            # Registrar en bitácora: Placa detectada pero NO REGISTRADA
            registrar_bitacora(
                usuario=request.user,
                accion=Bitacora.Accion.CONSULTAR,
                modulo=Bitacora.Modulo.RECONOCIMIENTO_PLACAS,
                descripcion=f"Placa '{plate_raw}' detectada (confianza: {score*100:.1f}%) pero NO registrada en el sistema (cámara: {camera_id})",
                request=request
            )
        
        return Response({
            "status": "ok",
            "plate": plate_raw,
            "score": score,
            "match": bool(v_match),
            "vehiculo": VehiculoDetailSerializer(v_match).data if v_match else None,
            "ordenes_pendientes": ordenes_pendientes,
            "lectura": LecturaPlacaSerializer(lectura).data
        }, status=200)


def _norm(sim):
    try:
        sim = float(sim or 0.0)
    except:
        sim = 0.0
    return sim / 100.0 if sim > 1.0 else sim
