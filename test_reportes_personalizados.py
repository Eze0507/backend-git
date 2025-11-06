"""
Script de prueba para Reportes Personalizados (Fase 2)
"""
import requests
import json

BASE_URL = "http://localhost:8000"

# Obtener token de autenticación
def login():
    response = requests.post(
        f"{BASE_URL}/api/auth/login/",
        json={
            "username": "superadmin",
            "password": "admin123"
        }
    )
    if response.status_code == 200:
        return response.json().get('access')
    return None

def test_obtener_entidades(token):
    """
    Prueba: Obtener entidades disponibles
    GET /api/ia/reportes/entidades/
    """
    print("\n" + "="*60)
    print("PRUEBA 1: Obtener Entidades Disponibles")
    print("="*60)
    
    response = requests.get(
        f"{BASE_URL}/api/ia/reportes/entidades/",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Success: {data.get('success')}")
        print(f"\nEntidades disponibles: {len(data.get('entidades', {}))}")
        for key, config in data.get('entidades', {}).items():
            print(f"\n  - {key}:")
            print(f"    Nombre: {config.get('nombre')}")
            print(f"    Campos: {len(config.get('campos_disponibles', {}))}")
            print(f"    Filtros: {len(config.get('filtros_disponibles', {}))}")
    else:
        print(f"✗ Error: {response.text}")
    
    return response

def test_generar_reporte_ordenes(token):
    """
    Prueba: Generar reporte personalizado de órdenes
    POST /api/ia/reportes/generar-personalizado/
    """
    print("\n" + "="*60)
    print("PRUEBA 2: Generar Reporte Personalizado - Órdenes")
    print("="*60)
    
    payload = {
        "nombre": "Órdenes Pendientes con Cliente",
        "entidad": "ordenes",
        "campos": [
            "id",
            "fecha_creacion",
            "estado",
            "cliente__nombre",
            "cliente__apellido",
            "total"
        ],
        "filtros": {
            "estado": "pendiente"
        },
        "ordenamiento": ["-fecha_creacion"],
        "formato": "PDF"
    }
    
    print(f"\nPayload:")
    print(json.dumps(payload, indent=2))
    
    response = requests.post(
        f"{BASE_URL}/api/ia/reportes/generar-personalizado/",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    print(f"\nStatus: {response.status_code}")
    
    if response.status_code == 201:
        data = response.json()
        print(f"✓ Success: {data.get('success')}")
        print(f"✓ Message: {data.get('message')}")
        
        reporte = data.get('reporte', {})
        print(f"\nReporte generado:")
        print(f"  - ID: {reporte.get('id')}")
        print(f"  - Nombre: {reporte.get('nombre')}")
        print(f"  - Tipo: {reporte.get('tipo_display')}")
        print(f"  - Formato: {reporte.get('formato_display')}")
        print(f"  - Registros: {reporte.get('registros_procesados')}")
        print(f"  - Tiempo: {reporte.get('tiempo_generacion')}s")
        print(f"  - Archivo: {reporte.get('archivo')}")
    else:
        print(f"✗ Error: {response.text}")
    
    return response

def test_generar_reporte_clientes(token):
    """
    Prueba: Generar reporte personalizado de clientes
    """
    print("\n" + "="*60)
    print("PRUEBA 3: Generar Reporte Personalizado - Clientes")
    print("="*60)
    
    payload = {
        "nombre": "Clientes Registrados Este Año",
        "entidad": "clientes",
        "campos": [
            "id",
            "nombre",
            "apellido",
            "telefono",
            "email",
            "tipo_cliente",
            "created_at"
        ],
        "filtros": {
            "created_at__gte": "2025-01-01"
        },
        "ordenamiento": ["-created_at"],
        "formato": "XLSX"
    }
    
    print(f"\nPayload:")
    print(json.dumps(payload, indent=2))
    
    response = requests.post(
        f"{BASE_URL}/api/ia/reportes/generar-personalizado/",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    print(f"\nStatus: {response.status_code}")
    
    if response.status_code == 201:
        data = response.json()
        print(f"✓ Success: {data.get('success')}")
        
        reporte = data.get('reporte', {})
        print(f"\nReporte generado:")
        print(f"  - ID: {reporte.get('id')}")
        print(f"  - Formato: {reporte.get('formato_display')}")
        print(f"  - Registros: {reporte.get('registros_procesados')}")
        print(f"  - Archivo: {reporte.get('archivo')}")
    else:
        print(f"✗ Error: {response.text}")
    
    return response

def test_generar_reporte_vehiculos(token):
    """
    Prueba: Generar reporte personalizado de vehículos
    """
    print("\n" + "="*60)
    print("PRUEBA 4: Generar Reporte Personalizado - Vehículos")
    print("="*60)
    
    payload = {
        "nombre": "Vehículos por Año",
        "entidad": "vehiculos",
        "campos": [
            "numero_placa",
            "marca__nombre",
            "modelo__nombre",
            "anio",
            "color",
            "cliente__nombre",
            "cliente__telefono"
        ],
        "filtros": {
            "anio__gte": 2020
        },
        "ordenamiento": ["-anio", "marca__nombre"],
        "formato": "PDF"
    }
    
    print(f"\nPayload:")
    print(json.dumps(payload, indent=2))
    
    response = requests.post(
        f"{BASE_URL}/api/ia/reportes/generar-personalizado/",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    print(f"\nStatus: {response.status_code}")
    
    if response.status_code == 201:
        data = response.json()
        print(f"✓ Success: {data.get('success')}")
        
        reporte = data.get('reporte', {})
        print(f"\nReporte generado:")
        print(f"  - ID: {reporte.get('id')}")
        print(f"  - Registros: {reporte.get('registros_procesados')}")
        print(f"  - Archivo: {reporte.get('archivo')}")
    else:
        print(f"✗ Error: {response.text}")
    
    return response

def test_validacion_campos_invalidos(token):
    """
    Prueba: Validar que rechace campos inválidos
    """
    print("\n" + "="*60)
    print("PRUEBA 5: Validación de Campos Inválidos")
    print("="*60)
    
    payload = {
        "nombre": "Reporte con campos inválidos",
        "entidad": "ordenes",
        "campos": [
            "id",
            "campo_inexistente",  # Este campo no existe
            "otro_campo_falso"    # Este tampoco
        ],
        "formato": "PDF"
    }
    
    print(f"\nPayload (con campos inválidos):")
    print(json.dumps(payload, indent=2))
    
    response = requests.post(
        f"{BASE_URL}/api/ia/reportes/generar-personalizado/",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    print(f"\nStatus: {response.status_code}")
    
    if response.status_code == 400:
        data = response.json()
        print(f"✓ Validación funcionó correctamente")
        print(f"✓ Error esperado: {data.get('errors')}")
    else:
        print(f"✗ Debería haber rechazado los campos inválidos")
    
    return response

def main():
    print("\n" + "="*60)
    print("PRUEBAS DE REPORTES PERSONALIZADOS (FASE 2)")
    print("="*60)
    
    # Login
    print("\n🔐 Obteniendo token de autenticación...")
    token = login()
    
    if not token:
        print("✗ Error: No se pudo autenticar")
        return
    
    print("✓ Token obtenido")
    
    # Ejecutar pruebas
    test_obtener_entidades(token)
    test_generar_reporte_ordenes(token)
    test_generar_reporte_clientes(token)
    test_generar_reporte_vehiculos(token)
    test_validacion_campos_invalidos(token)
    
    print("\n" + "="*60)
    print("✅ TODAS LAS PRUEBAS COMPLETADAS")
    print("="*60)
    print("\nRevisa los archivos generados en: backend-git/media/reportes/")

if __name__ == "__main__":
    main()
