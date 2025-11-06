"""
Whitelist de entidades, campos y filtros disponibles para reportes personalizados
Define qué datos pueden ser consultados de forma segura
"""

ENTIDADES_DISPONIBLES = {
    'ordenes': {
        'nombre': 'Órdenes de Trabajo',
        'nombre_modelo': 'Orden de Trabajo',
        'modelo': 'operaciones_inventario.OrdenTrabajo',
        'campos_disponibles': {
            'id': {'label': 'ID', 'tipo': 'number'},
            'fecha_creacion': {'label': 'Fecha de Creación', 'tipo': 'datetime'},
            'fecha_actualizacion': {'label': 'Última Actualización', 'tipo': 'datetime'},
            'fecha_cierre': {'label': 'Fecha de Cierre', 'tipo': 'datetime'},
            'estado': {'label': 'Estado', 'tipo': 'text'},
            'fallo_requerimiento': {'label': 'Fallo/Requerimiento', 'tipo': 'text'},
            'total': {'label': 'Total (Bs.)', 'tipo': 'decimal'},
            'cliente__nombre': {'label': 'Cliente - Nombre', 'tipo': 'text'},
            'cliente__apellido': {'label': 'Cliente - Apellido', 'tipo': 'text'},
            'cliente__telefono': {'label': 'Cliente - Teléfono', 'tipo': 'text'},
            'cliente__nit': {'label': 'Cliente - NIT', 'tipo': 'text'},
            'cliente__email': {'label': 'Cliente - Email', 'tipo': 'text'},
            'vehiculo__numero_placa': {'label': 'Vehículo - Placa', 'tipo': 'text'},
            'vehiculo__marca__nombre': {'label': 'Vehículo - Marca', 'tipo': 'text'},
            'vehiculo__modelo__nombre': {'label': 'Vehículo - Modelo', 'tipo': 'text'},
            'vehiculo__año': {'label': 'Vehículo - Año', 'tipo': 'number'},
            'vehiculo__color': {'label': 'Vehículo - Color', 'tipo': 'text'},
            'tecnico__first_name': {'label': 'Técnico - Nombre', 'tipo': 'text'},
            'tecnico__last_name': {'label': 'Técnico - Apellido', 'tipo': 'text'},
        },
        'filtros_disponibles': {
            'estado': {
                'label': 'Estado',
                'tipo': 'choice',
                'opciones': [
                    {'value': 'pendiente', 'label': 'Pendiente'},
                    {'value': 'en_proceso', 'label': 'En Proceso'},
                    {'value': 'completada', 'label': 'Completada'},
                    {'value': 'cancelada', 'label': 'Cancelada'},
                ]
            },
            'fecha_creacion__gte': {
                'label': 'Fecha de creación desde',
                'tipo': 'date',
                'placeholder': 'DD/MM/YYYY'
            },
            'fecha_creacion__lte': {
                'label': 'Fecha de creación hasta',
                'tipo': 'date',
                'placeholder': 'DD/MM/YYYY'
            },
            'fecha_cierre__gte': {
                'label': 'Fecha de cierre desde',
                'tipo': 'date',
                'placeholder': 'DD/MM/YYYY'
            },
            'fecha_cierre__lte': {
                'label': 'Fecha de cierre hasta',
                'tipo': 'date',
                'placeholder': 'DD/MM/YYYY'
            },
            'total__gte': {
                'label': 'Total mínimo (Bs.)',
                'tipo': 'number',
                'placeholder': '0.00'
            },
            'total__lte': {
                'label': 'Total máximo (Bs.)',
                'tipo': 'number',
                'placeholder': '0.00'
            },
            'cliente__nombre__icontains': {
                'label': 'Cliente contiene',
                'tipo': 'text',
                'placeholder': 'Nombre del cliente'
            },
            'vehiculo__numero_placa__icontains': {
                'label': 'Placa contiene',
                'tipo': 'text',
                'placeholder': 'Número de placa'
            },
        }
    },
    
    'clientes': {
        'nombre': 'Clientes',
        'nombre_modelo': 'Cliente',
        'modelo': 'clientes_servicios.Cliente',
        'campos_disponibles': {
            'id': {'label': 'ID', 'tipo': 'number'},
            'nombre': {'label': 'Nombre', 'tipo': 'text'},
            'apellido': {'label': 'Apellido', 'tipo': 'text'},
            'nit': {'label': 'NIT', 'tipo': 'text'},
            'telefono': {'label': 'Teléfono', 'tipo': 'text'},
            'email': {'label': 'Email', 'tipo': 'text'},
            'direccion': {'label': 'Dirección', 'tipo': 'text'},
            'tipo_cliente': {'label': 'Tipo de Cliente', 'tipo': 'text'},
            'created_at': {'label': 'Fecha de Registro', 'tipo': 'datetime'},
            'updated_at': {'label': 'Última Actualización', 'tipo': 'datetime'},
        },
        'filtros_disponibles': {
            'tipo_cliente': {
                'label': 'Tipo de Cliente',
                'tipo': 'choice',
                'opciones': [
                    {'value': 'NATURAL', 'label': 'Persona Natural'},
                    {'value': 'EMPRESA', 'label': 'Empresa'},
                ]
            },
            'created_at__gte': {
                'label': 'Registrado desde',
                'tipo': 'date',
                'placeholder': 'DD/MM/YYYY'
            },
            'created_at__lte': {
                'label': 'Registrado hasta',
                'tipo': 'date',
                'placeholder': 'DD/MM/YYYY'
            },
            'nombre__icontains': {
                'label': 'Nombre contiene',
                'tipo': 'text',
                'placeholder': 'Buscar por nombre'
            },
            'apellido__icontains': {
                'label': 'Apellido contiene',
                'tipo': 'text',
                'placeholder': 'Buscar por apellido'
            },
            'nit__icontains': {
                'label': 'NIT contiene',
                'tipo': 'text',
                'placeholder': 'Buscar por NIT'
            },
        }
    },
    
    'vehiculos': {
        'nombre': 'Vehículos',
        'nombre_modelo': 'Vehículo',
        'modelo': 'operaciones_inventario.Vehiculo',
        'campos_disponibles': {
            'id': {'label': 'ID', 'tipo': 'number'},
            'numero_placa': {'label': 'Número de Placa', 'tipo': 'text'},
            'marca__nombre': {'label': 'Marca', 'tipo': 'text'},
            'modelo__nombre': {'label': 'Modelo', 'tipo': 'text'},
            'año': {'label': 'Año', 'tipo': 'number'},
            'color': {'label': 'Color', 'tipo': 'text'},
            'tipo': {'label': 'Tipo', 'tipo': 'text'},
            'vin': {'label': 'VIN', 'tipo': 'text'},
            'cliente__nombre': {'label': 'Propietario - Nombre', 'tipo': 'text'},
            'cliente__apellido': {'label': 'Propietario - Apellido', 'tipo': 'text'},
            'cliente__telefono': {'label': 'Propietario - Teléfono', 'tipo': 'text'},
            'cliente__email': {'label': 'Propietario - Email', 'tipo': 'text'},
        },
        'filtros_disponibles': {
            'año__gte': {
                'label': 'Año desde',
                'tipo': 'number',
                'placeholder': '2000'
            },
            'año__lte': {
                'label': 'Año hasta',
                'tipo': 'number',
                'placeholder': '2025'
            },
            'marca__nombre__icontains': {
                'label': 'Marca contiene',
                'tipo': 'text',
                'placeholder': 'Toyota, Nissan, etc.'
            },
            'modelo__nombre__icontains': {
                'label': 'Modelo contiene',
                'tipo': 'text',
                'placeholder': 'Corolla, Sentra, etc.'
            },
            'numero_placa__icontains': {
                'label': 'Placa contiene',
                'tipo': 'text',
                'placeholder': 'Número de placa'
            },
            'color__icontains': {
                'label': 'Color contiene',
                'tipo': 'text',
                'placeholder': 'Blanco, Negro, etc.'
            },
        }
    },
    
    'items': {
        'nombre': 'Items y Repuestos',
        'nombre_modelo': 'Item',
        'modelo': 'operaciones_inventario.Item',
        'campos_disponibles': {
            'id': {'label': 'ID', 'tipo': 'number'},
            'codigo': {'label': 'Código', 'tipo': 'text'},
            'nombre': {'label': 'Nombre', 'tipo': 'text'},
            'descripcion': {'label': 'Descripción', 'tipo': 'text'},
            'tipo': {'label': 'Tipo', 'tipo': 'text'},
            'fabricante': {'label': 'Fabricante', 'tipo': 'text'},
            'precio': {'label': 'Precio de Venta (Bs.)', 'tipo': 'decimal'},
            'costo': {'label': 'Costo/Precio de Compra (Bs.)', 'tipo': 'decimal'},
            'stock': {'label': 'Stock', 'tipo': 'number'},
            'estado': {'label': 'Estado', 'tipo': 'text'},
            'area__nombre': {'label': 'Área', 'tipo': 'text'},
        },
        'filtros_disponibles': {
            'tipo': {
                'label': 'Tipo de Item',
                'tipo': 'choice',
                'opciones': [
                    {'value': 'Item de venta', 'label': 'Item de venta'},
                    {'value': 'Item de taller', 'label': 'Item de taller'},
                    {'value': 'Servicio', 'label': 'Servicio'},
                ]
            },
            'estado': {
                'label': 'Estado',
                'tipo': 'choice',
                'opciones': [
                    {'value': 'Disponible', 'label': 'Disponible'},
                    {'value': 'No disponible', 'label': 'No disponible'},
                ]
            },
            'stock__lt': {
                'label': 'Stock menor a',
                'tipo': 'number',
                'placeholder': 'Cantidad'
            },
            'stock__lte': {
                'label': 'Stock menor o igual a',
                'tipo': 'number',
                'placeholder': 'Cantidad'
            },
            'stock__gte': {
                'label': 'Stock mayor o igual a',
                'tipo': 'number',
                'placeholder': 'Cantidad'
            },
            'precio__gte': {
                'label': 'Precio mínimo (Bs.)',
                'tipo': 'number',
                'placeholder': '0.00'
            },
            'precio__lte': {
                'label': 'Precio máximo (Bs.)',
                'tipo': 'number',
                'placeholder': '0.00'
            },
            'costo__gte': {
                'label': 'Costo mínimo (Bs.)',
                'tipo': 'number',
                'placeholder': '0.00'
            },
            'costo__lte': {
                'label': 'Costo máximo (Bs.)',
                'tipo': 'number',
                'placeholder': '0.00'
            },
            'nombre__icontains': {
                'label': 'Nombre contiene',
                'tipo': 'text',
                'placeholder': 'Buscar por nombre'
            },
            'codigo__icontains': {
                'label': 'Código contiene',
                'tipo': 'text',
                'placeholder': 'Buscar por código'
            },
            'fabricante__icontains': {
                'label': 'Fabricante contiene',
                'tipo': 'text',
                'placeholder': 'Buscar por fabricante'
            },
        }
    },
}


def obtener_entidades():
    """
    Retorna la lista de entidades disponibles con sus metadatos
    """
    return {
        key: {
            'id': key,
            'nombre': config['nombre'],
            'nombre_modelo': config['nombre_modelo'],
            'total_campos': len(config['campos_disponibles']),
            'total_filtros': len(config['filtros_disponibles'])
        }
        for key, config in ENTIDADES_DISPONIBLES.items()
    }


def obtener_config_entidad(entidad_id):
    """
    Obtiene la configuración completa de una entidad
    
    Args:
        entidad_id: ID de la entidad (ordenes, clientes, etc.)
    
    Returns:
        Dict con la configuración o None si no existe
    """
    return ENTIDADES_DISPONIBLES.get(entidad_id)


def validar_campos(entidad_id, campos):
    """
    Valida que los campos estén en la whitelist
    
    Args:
        entidad_id: ID de la entidad
        campos: Lista de campos a validar
    
    Returns:
        Tuple (valido: bool, campos_invalidos: list)
    """
    config = obtener_config_entidad(entidad_id)
    if not config:
        return False, []
    
    campos_permitidos = set(config['campos_disponibles'].keys())
    campos_invalidos = [c for c in campos if c not in campos_permitidos]
    
    return len(campos_invalidos) == 0, campos_invalidos


def validar_filtros(entidad_id, filtros):
    """
    Valida que los filtros estén en la whitelist
    
    Args:
        entidad_id: ID de la entidad
        filtros: Dict de filtros a validar
    
    Returns:
        Tuple (valido: bool, filtros_invalidos: list)
    """
    config = obtener_config_entidad(entidad_id)
    if not config:
        return False, []
    
    filtros_permitidos = set(config['filtros_disponibles'].keys())
    filtros_invalidos = [f for f in filtros.keys() if f not in filtros_permitidos]
    
    return len(filtros_invalidos) == 0, filtros_invalidos
