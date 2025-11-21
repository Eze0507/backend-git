# App Backup/Restore

Sistema de backup y restauración para el ERP de taller automotriz con soporte multi-tenant.

## Descripción

Esta app permite a cada taller (tenant) hacer copias de seguridad de todos sus datos y restaurarlos cuando sea necesario. El sistema es completamente multi-tenant, asegurando que cada taller solo pueda acceder a sus propios datos.

## Características

- ✅ **Multi-tenant**: Cada taller solo puede hacer backup/restore de sus propios datos
- ✅ **Descarga directa**: Los backups se descargan como archivos JSON
- ✅ **Restauración desde archivo**: Permite restaurar desde archivos JSON descargados
- ✅ **Seguridad**: Solo administradores o propietarios pueden restaurar
- ✅ **Registro en bitácora**: Todas las operaciones se registran
- ✅ **Transacciones**: Rollback automático si falla la restauración

## Endpoints

### Crear Backup
```
GET /api/backup/
Headers: Authorization: Bearer <token>
Response: Archivo JSON descargable
```

### Restaurar Backup
```
POST /api/restore/
Headers: Authorization: Bearer <token>
Body: FormData
  - backup_file: Archivo JSON (requerido)
  - replace: true/false (opcional, default: false)
Response: JSON con resumen de la restauración
```

## Estructura de Archivos

```
backup_restore/
├── __init__.py
├── apps.py          # Configuración de la app
├── urls.py          # URLs del módulo
├── views.py         # Vistas de backup y restore
├── utils.py         # Funciones de exportación/importación
├── models.py        # (vacío, no requiere modelos propios)
├── admin.py         # (vacío)
└── tests.py         # (para futuros tests)
```

## Uso

### Crear un Backup

```python
# Con axios
const response = await axios.get('/api/backup/', {
  headers: {
    'Authorization': `Bearer ${token}`
  },
  responseType: 'blob'
});

const url = window.URL.createObjectURL(new Blob([response.data]));
const link = document.createElement('a');
link.href = url;
link.setAttribute('download', `backup_${Date.now()}.json`);
document.body.appendChild(link);
link.click();
```

### Restaurar un Backup

```python
# Con axios
const formData = new FormData();
formData.append('backup_file', file);
formData.append('replace', false);

const response = await axios.post('/api/restore/', formData, {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'multipart/form-data'
  }
});
```

## Datos Incluidos en el Backup

El backup incluye todos los datos del tenant:

- Información del Tenant
- Cargos y Empleados
- Clientes y Citas
- Vehículos (con Marcas y Modelos)
- Áreas, Items, Proveedores
- Presupuestos y Detalles
- Órdenes de Trabajo y todos sus detalles
- Pagos
- Facturas de Proveedor
- Lecturas de Placa
- Reportes (metadatos)
- Bitácoras

## Notas Importantes

1. **Usuarios**: Los usuarios no se restauran automáticamente por seguridad
2. **Archivos**: Las imágenes y archivos no se restauran (solo metadatos)
3. **Stripe**: Los IDs de Stripe no se restauran
4. **Bitácoras**: Las bitácoras se exportan pero no se restauran (pueden ser muy grandes)

## Seguridad

- Requiere autenticación JWT
- Solo administradores o propietarios pueden restaurar
- Cada tenant solo puede acceder a sus propios datos
- Todas las operaciones se registran en bitácora

## Dependencias

- `personal_admin`: Para acceder a modelos Tenant, Bitacora, etc.
- `clientes_servicios`: Para modelos Cliente, Cita
- `operaciones_inventario`: Para modelos de inventario y órdenes
- `finanzas_facturacion`: Para modelos de pagos y facturas
- `servicios_IA`: Para modelos de reconocimiento y reportes

