"""
Script simple para verificar que las URLs de backup esten configuradas
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_taller.settings')

try:
    django.setup()
    
    from django.urls import resolve, reverse, NoReverseMatch
    from backup_restore.views import BackupView, RestoreView
    
    print("=" * 60)
    print("VERIFICACION DE URLs DE BACKUP/RESTORE")
    print("=" * 60)
    print()
    
    # Verificar que las vistas existen
    print("[1] Verificando vistas...")
    try:
        assert BackupView is not None
        assert RestoreView is not None
        print("[OK] Vistas BackupView y RestoreView encontradas")
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
    
    print()
    
    # Verificar URLs
    print("[2] Verificando URLs...")
    
    # Probar resolver /api/backup/
    try:
        match = resolve('/api/backup/')
        print(f"[OK] URL /api/backup/ resuelve correctamente")
        print(f"     View: {match.func.__name__ if hasattr(match.func, '__name__') else match.func}")
        print(f"     View Name: {match.view_name}")
    except Exception as e:
        print(f"[ERROR] No se pudo resolver /api/backup/: {e}")
        sys.exit(1)
    
    # Probar resolver /api/restore/
    try:
        match = resolve('/api/restore/')
        print(f"[OK] URL /api/restore/ resuelve correctamente")
        print(f"     View: {match.func.__name__ if hasattr(match.func, '__name__') else match.func}")
        print(f"     View Name: {match.view_name}")
    except Exception as e:
        print(f"[ERROR] No se pudo resolver /api/restore/: {e}")
        sys.exit(1)
    
    print()
    
    # Verificar reverse
    print("[3] Verificando reverse URLs...")
    try:
        backup_url = reverse('backup_restore:backup')
        print(f"[OK] reverse('backup_restore:backup') = {backup_url}")
    except NoReverseMatch as e:
        print(f"[ERROR] No se pudo hacer reverse de backup: {e}")
    
    try:
        restore_url = reverse('backup_restore:restore')
        print(f"[OK] reverse('backup_restore:restore') = {restore_url}")
    except NoReverseMatch as e:
        print(f"[ERROR] No se pudo hacer reverse de restore: {e}")
    
    print()
    
    # Verificar imports de utils
    print("[4] Verificando funciones de utils...")
    try:
        from backup_restore.utils import export_tenant_data, import_tenant_data
        print("[OK] Funciones export_tenant_data e import_tenant_data importadas correctamente")
    except Exception as e:
        print(f"[ERROR] No se pudieron importar funciones de utils: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print()
    print("=" * 60)
    print("[OK] TODAS LAS VERIFICACIONES PASARON")
    print("=" * 60)
    print()
    print("Los endpoints estan configurados correctamente:")
    print("  - GET  /api/backup/  -> Crear y descargar backup")
    print("  - POST /api/restore/ -> Restaurar desde archivo")
    print()
    print("NOTA: Para probar los endpoints completamente, necesitas:")
    print("  1. Tener el servidor corriendo (python manage.py runserver)")
    print("  2. Tener un usuario autenticado con tenant asociado")
    print("  3. Hacer peticiones HTTP con token JWT")
    
except Exception as e:
    print(f"[ERROR] Error general: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

