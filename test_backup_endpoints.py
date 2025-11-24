"""
Script de prueba para los endpoints de Backup/Restore
Ejecutar: python test_backup_endpoints.py
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_taller.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from personal_admin.models_saas import Tenant, UserProfile
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
import json
from django.conf import settings

def test_backup_endpoints():
    """Prueba los endpoints de backup y restore"""
    
    print("=" * 60)
    print("PRUEBA DE ENDPOINTS DE BACKUP/RESTORE")
    print("=" * 60)
    
    # Verificar que existe al menos un usuario y tenant
    try:
        user = User.objects.first()
        if not user:
            print("[ERROR] No hay usuarios en la base de datos. Crea un usuario primero.")
            return
        
        if not hasattr(user, 'profile'):
            print("[ERROR] El usuario no tiene perfil. Asegurate de que tenga un UserProfile.")
            return
        
        tenant = user.profile.tenant
        print(f"[OK] Usuario de prueba: {user.username}")
        print(f"[OK] Tenant: {tenant.nombre_taller}")
        print()
        
    except Exception as e:
        print(f"[ERROR] Error al obtener usuario/tenant: {e}")
        return
    
    # Crear cliente API
    client = APIClient()
    # Asegurarnos que el host utilizado por el cliente de pruebas está permitido
    # (el cliente de pruebas usa 'testserver' como HTTP_HOST por defecto)
    if 'testserver' not in settings.ALLOWED_HOSTS:
        settings.ALLOWED_HOSTS.append('testserver')
    
    # Obtener token JWT
    try:
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        print("[OK] Token JWT generado correctamente")
        print()
    except Exception as e:
        print(f"❌ Error al generar token: {e}")
        return
    
    # Variable para guardar backup
    backup_file_content = None
    
    # Prueba 1: GET /api/backup/
    print("-" * 60)
    print("PRUEBA 1: Crear Backup (GET /api/backup/)")
    print("-" * 60)
    try:
        response = client.get('/api/backup/')
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("[OK] Backup creado exitosamente")
            print(f"Content-Type: {response.get('Content-Type')}")
            print(f"Content-Disposition: {response.get('Content-Disposition')}")
            
            # Verificar que es JSON válido
            try:
                import gzip
                # Detectar si está comprimido con gzip
                if response.content[:2] == b'\x1f\x8b':
                    print("[OK] Archivo comprimido con gzip")
                    content = gzip.decompress(response.content).decode('utf-8')
                else:
                    content = response.content.decode('utf-8')
                backup_data = json.loads(content)
                print(f"[OK] JSON valido")
                print(f"   - Version: {backup_data.get('metadata', {}).get('version')}")
                print(f"   - Tenant: {backup_data.get('metadata', {}).get('tenant_nombre')}")
                print(f"   - Fecha: {backup_data.get('metadata', {}).get('fecha_backup')}")
                print(f"   - Cargos: {len(backup_data.get('cargos', []))}")
                print(f"   - Clientes: {len(backup_data.get('clientes', []))}")
                print(f"   - Vehiculos: {len(backup_data.get('vehiculos', []))}")
                print(f"   - Ordenes: {len(backup_data.get('ordenes_trabajo', []))}")
                
                # Guardar backup para prueba de restore
                backup_file_content = content
                # Verificar que Content-Length coincide
                content_length_header = response.get('Content-Length')
                if content_length_header:
                    try:
                        content_length_header_int = int(content_length_header)
                        if content_length_header_int == len(content.encode('utf-8')):
                            print("[OK] Content-Length coincide con el tamaño del JSON")
                        else:
                            print(f"[WARN] Content-Length ({content_length_header_int}) no coincide con longitud real ({len(content.encode('utf-8'))})")
                    except ValueError:
                        print("[WARN] Content-Length presente pero no es entero")

                # Verificar Content-Disposition con nombre de archivo
                content_disposition = response.get('Content-Disposition', '')
                if 'filename="backup_' in content_disposition:
                    print('[OK] Content-Disposition con filename correcto')
                else:
                    print('[WARN] Content-Disposition no tiene filename esperado')
                print()
                print("[OK] Backup guardado en memoria para prueba de restore")
                
            except json.JSONDecodeError as e:
                print(f"[ERROR] El contenido no es JSON valido: {e}")
        else:
            print(f"[ERROR] Status: {response.status_code}")
            if hasattr(response, 'data'):
                print(f"   Respuesta: {response.data}")
            else:
                try:
                    print(f"   Respuesta: {response.content.decode('utf-8')[:200]}")
                except:
                    print(f"   Respuesta: {response.content[:200]}")
            
    except Exception as e:
        print(f"[ERROR] Error al crear backup: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Prueba 2: POST /api/restore/ (solo si el usuario es admin/propietario y tenemos backup)
    print("-" * 60)
    print("PRUEBA 2: Restaurar Backup (POST /api/restore/)")
    print("-" * 60)
    
    if not backup_file_content:
        print("[WARNING] No se pudo crear backup, saltando prueba de restore...")
    elif not (user.is_staff or user.is_superuser or tenant.propietario == user):
        print("[WARNING] Usuario no tiene permisos para restaurar (solo admin/propietario)")
        print("   Saltando prueba de restore...")
    else:
        try:
            # Crear un archivo temporal con el backup
            from django.core.files.uploadedfile import SimpleUploadedFile
            
            backup_file = SimpleUploadedFile(
                "test_backup.json",
                backup_file_content.encode('utf-8'),
                content_type='application/json'
            )
            
            response = client.post('/api/restore/', {
                'backup_file': backup_file,
                'replace': 'true'  # Probar replace=true con el fix usando Django ORM
            }, format='multipart')
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("[OK] Backup restaurado exitosamente")
                if hasattr(response, 'data'):
                    summary = response.data.get('summary', {})
                    print(f"   Resumen de restauracion:")
                    for key, value in summary.items():
                        if isinstance(value, int) and value > 0:
                            print(f"   - {key}: {value}")
            else:
                print(f"[ERROR] Status: {response.status_code}")
                if hasattr(response, 'data'):
                    print(f"   Respuesta: {response.data}")
                else:
                    try:
                        print(f"   Respuesta: {response.content.decode('utf-8')[:200]}")
                    except:
                        print(f"   Respuesta: {response.content[:200]}")
                    
        except Exception as e:
            print(f"[ERROR] Error al restaurar backup: {e}")
            import traceback
            traceback.print_exc()
    
    print()
    print("=" * 60)
    print("PRUEBAS COMPLETADAS")
    print("=" * 60)

if __name__ == '__main__':
    test_backup_endpoints()

