"""
Configuración de reportes estáticos disponibles
Define qué reportes se pueden generar y qué datos necesitan
"""

REPORTES_ESTATICOS = {
    'ordenes_estado': {
        'nombre': 'Órdenes de Trabajo por Estado',
        'descripcion': 'Lista de todas las órdenes agrupadas por estado',
        'modelo': 'operaciones_inventario.OrdenTrabajo',
        'campos': [
            'id', 
            'fecha_creacion', 
            'cliente__nombre', 
            'cliente__apellido',
            'vehiculo__numero_placa', 
            'vehiculo__marca__nombre',
            'vehiculo__modelo__nombre',
            'estado', 
            'fallo_requerimiento',
            'total'
        ],
        'filtros_default': {}  # Sin filtros por defecto, muestra todas las órdenes
    },
    
    'ordenes_pendientes': {
        'nombre': 'Órdenes Pendientes y En Proceso',
        'descripcion': 'Órdenes que requieren atención',
        'modelo': 'operaciones_inventario.OrdenTrabajo',
        'campos': [
            'id',
            'fecha_creacion',
            'cliente__nombre',
            'cliente__apellido',
            'cliente__telefono',
            'vehiculo__numero_placa',
            'vehiculo__marca__nombre',
            'estado',
            'fallo_requerimiento',
            'total',
        ],
        'filtros_default': {
            'estado__in': ['pendiente', 'en_proceso']
        }
    },
    
    'ordenes_completadas_mes': {
        'nombre': 'Órdenes Completadas del Mes',
        'descripcion': 'Órdenes completadas en el mes actual',
        'modelo': 'operaciones_inventario.OrdenTrabajo',
        'campos': [
            'id',
            'fecha_creacion',
            'fecha_finalizacion',
            'cliente__nombre',
            'cliente__apellido',
            'vehiculo__numero_placa',
            'vehiculo__marca__nombre',
            'vehiculo__modelo__nombre',
            'fallo_requerimiento',
            'estado',
            'total',
        ],
        'filtros_default': {
            'estado__in': ['finalizada', 'entregada'],
            'fecha_creacion__month': 'mes_actual',
            'fecha_creacion__year': 'anio_actual'
        }
    },
    
    'ingresos_mensual': {
        'nombre': 'Resumen de Ingresos Mensual',
        'descripcion': 'Análisis financiero del mes',
        'modelo': 'operaciones_inventario.OrdenTrabajo',
        'campos': [
            'id',
            'fecha_creacion',
            'fecha_finalizacion',
            'cliente__nombre',
            'cliente__apellido',
            'subtotal',
            'descuento',
            'impuesto',
            'total',
            'estado',
            'pago',
        ],
        'filtros_default': {
            'estado__in': ['finalizada', 'entregada'],
            'fecha_creacion__month': 'mes_actual',
            'fecha_creacion__year': 'anio_actual'
        }
    },
    
    'items_criticos': {
        'nombre': 'Items con Stock Crítico',
        'descripcion': 'Repuestos que requieren reabastecimiento',
        'modelo': 'operaciones_inventario.Item',
        'campos': [
            'id',
            'codigo',
            'nombre',
            'tipo',
            'stock',
            'costo',
            'precio',
            'estado',
        ],
        'filtros_default': {
            'stock__lt': 10,
            'tipo__in': ['Item de venta', 'Item de taller']
        }
    },
}


def obtener_config_reporte(tipo_reporte):
    """
    Obtiene la configuración de un reporte estático
    
    Args:
        tipo_reporte: Clave del reporte (ej: 'ordenes_estado')
    
    Returns:
        Dict con la configuración o None si no existe
    """
    return REPORTES_ESTATICOS.get(tipo_reporte)


def listar_reportes_disponibles():
    """
    Retorna lista de reportes disponibles con su info básica
    
    Returns:
        Lista de diccionarios con: id, nombre, descripcion
    """
    return [
        {
            'id': key,
            'nombre': config['nombre'],
            'descripcion': config['descripcion']
        }
        for key, config in REPORTES_ESTATICOS.items()
    ]
