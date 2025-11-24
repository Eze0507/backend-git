"""
Vistas para Backup y Restore del sistema multi-tenant.
"""
import json
import gzip
import logging
from django.http import HttpResponse
from django.utils import timezone
from django.core.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser

from .utils import export_tenant_data, import_tenant_data
from personal_admin.views import registrar_bitacora
from personal_admin.models import Bitacora

logger = logging.getLogger(__name__)


class BackupView(APIView):
    """
    Vista para crear un backup de todos los datos del tenant actual.
    Devuelve un archivo JSON descargable.
    
    GET /api/backup/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            user = request.user
            if not hasattr(user, 'profile') or not user.profile.tenant:
                return Response(
                    {"error": "Usuario no tiene un tenant asociado"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            tenant = user.profile.tenant
            
            # Exportar datos del tenant
            backup_data = export_tenant_data(tenant)
            
            # Convertir a JSON
            json_data = json.dumps(backup_data, indent=2, ensure_ascii=False)
            
            # Comprimir con gzip
            compressed_data = gzip.compress(json_data.encode('utf-8'))
            
            # Crear nombre de archivo con timestamp
            timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backup_{tenant.nombre_taller.replace(' ', '_')}_{timestamp}.json.gz"
            
            # Registrar en bitácora
            registrar_bitacora(
                usuario=user,
                accion=Bitacora.Accion.CREAR,
                modulo=Bitacora.Modulo.AUTENTICACION,
                descripcion=f"Backup del sistema creado: {filename}",
                request=request
            )
            
            # Crear respuesta HTTP con el archivo comprimido
            response = HttpResponse(compressed_data, content_type='application/gzip')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['Content-Length'] = len(compressed_data)
            
            return response
            
        except Exception as e:
            logger.error(f"Error al crear backup: {str(e)}", exc_info=True)
            return Response(
                {"error": f"Error al crear backup: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RestoreView(APIView):
    """
    Vista para restaurar datos desde un archivo de backup.
    Acepta un archivo JSON y restaura los datos al tenant actual.
    
    POST /api/restore/
    Body: FormData con 'backup_file' (archivo JSON) y opcionalmente 'replace' (true/false)
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def post(self, request):
        try:
            user = request.user
            if not hasattr(user, 'profile') or not user.profile.tenant:
                return Response(
                    {"error": "Usuario no tiene un tenant asociado"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            tenant = user.profile.tenant
            
            # Verificar que el usuario tenga permisos (solo admin o propietario)
            if not (user.is_staff or user.is_superuser or tenant.propietario == user):
                return Response(
                    {"error": "No tienes permisos para restaurar backups"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Obtener el archivo del request
            backup_file = request.FILES.get('backup_file')
            if not backup_file:
                # Intentar obtener desde data si viene como JSON
                if 'backup_data' in request.data:
                    backup_data = request.data['backup_data']
                    if isinstance(backup_data, str):
                        backup_data = json.loads(backup_data)
                else:
                    return Response(
                        {"error": "No se proporcionó archivo de backup"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                # Leer y parsear el archivo JSON (posiblemente comprimido)
                try:
                    file_content = backup_file.read()

                    # Detectar si el contenido está comprimido por gzip por los bytes mágicos
                    if isinstance(file_content, (bytes, bytearray)) and file_content[:2] == b'\x1f\x8b':
                        try:
                            file_content = gzip.decompress(file_content)
                        except (OSError, gzip.BadGzipFile) as e:
                            logger.error(f"Error al descomprimir gzip: {e}", exc_info=True)
                            return Response({"error": f"Error al descomprimir archivo gzip: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

                    # Intentar decodificar y parsear JSON
                    try:
                        backup_data = json.loads(file_content.decode('utf-8'))
                    except UnicodeDecodeError:
                        # Si no se puede decodificar, intentamos sin decodificar (ya dict)
                        try:
                            backup_data = json.loads(file_content)
                        except Exception as e:
                            logger.error(f"Error al parsear JSON: {e}", exc_info=True)
                            return Response({"error": f"Archivo JSON inválido: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

                except Exception as e:
                    logger.error(f"Error leyendo archivo de backup: {e}", exc_info=True)
                    return Response({"error": f"Archivo inválido: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Validar que el backup es válido
            if 'metadata' not in backup_data:
                return Response(
                    {"error": "Archivo de backup inválido: falta metadata"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verificar opción de reemplazo
            replace = request.data.get('replace', True)
            if isinstance(replace, str):
                replace = replace.lower() == 'true'
            
            # Importar datos
            summary = import_tenant_data(backup_data, tenant, replace=replace)
            
            # Registrar en bitácora
            registrar_bitacora(
                usuario=user,
                accion=Bitacora.Accion.EDITAR,
                modulo=Bitacora.Modulo.AUTENTICACION,
                descripcion=f"Restauración del sistema completada. Resumen: {json.dumps(summary)}",
                request=request
            )
            
            return Response(
                {
                    "message": "Backup restaurado exitosamente",
                    "summary": summary
                },
                status=status.HTTP_200_OK
            )
            
        except ValidationError as e:
            logger.error(f"Error de validación al restaurar backup: {str(e)}", exc_info=True)
            return Response(
                {"error": f"Error de validación: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error al restaurar backup: {str(e)}", exc_info=True)
            return Response(
                {"error": f"Error al restaurar backup: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
