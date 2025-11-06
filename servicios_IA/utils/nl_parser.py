"""
Parser de Lenguaje Natural para Reportes
Interpreta consultas en español y las convierte en filtros de base de datos
"""
import re
import dateparser
from datetime import datetime, timedelta
from django.utils import timezone
from .whitelist import ENTIDADES_DISPONIBLES


# Mapeo de palabras clave a entidades
KEYWORDS_ENTIDADES = {
    'ordenes': ['orden', 'ordenes', 'órdenes', 'trabajo', 'trabajos', 'ot', 'servicios'],
    'clientes': ['cliente', 'clientes'],
    'vehiculos': ['vehiculo', 'vehiculos', 'vehículo', 'vehículos', 'auto', 'autos', 'carro', 'carros'],
    'items': ['item', 'items', 'repuesto', 'repuestos', 'producto', 'productos', 'pieza', 'piezas'],
}

# Mapeo de estados
ESTADOS_ORDENES = {
    'pendiente': ['pendiente', 'pendientes', 'sin comenzar'],
    'en_proceso': ['en proceso', 'en progreso', 'trabajando', 'en curso'],
    'completada': ['completada', 'completadas', 'terminada', 'terminadas', 'finalizada', 'finalizadas'],
    'cancelada': ['cancelada', 'canceladas'],
}

# Mapeo de tipos de items
TIPOS_ITEMS = {
    'Item de venta': ['venta', 'ventas', 'para vender'],
    'Item de taller': ['taller', 'uso interno', 'herramienta', 'herramientas'],
    'Servicio': ['servicio', 'servicios'],
}

# Mapeo de comparadores numéricos
COMPARADORES = {
    'mayor': ['mayor', 'más', 'mas', 'superior', 'arriba'],
    'menor': ['menor', 'menos', 'inferior', 'abajo'],
    'igual': ['igual', 'exacto', 'exactamente'],
}


def detectar_entidad(consulta):
    """
    Detecta qué entidad está solicitando el usuario
    Prioriza la entidad que aparece primero y tiene más peso en la consulta
    
    Args:
        consulta: String con la consulta en lenguaje natural
    
    Returns:
        String con el ID de la entidad o None
    """
    consulta_lower = consulta.lower()
    
    # Buscar patrones que indiquen claramente la entidad principal
    # "dame/muestra/lista de X" donde X es la entidad principal
    patron_lista = r'(?:dame|muestra|lista|reporte|reportes?)\s+(?:de\s+)?(?:los?\s+|las?\s+)?(orden[e]?s?|cliente[s]?|vehiculo[s]?|vehículo[s]?|auto[s]?|item[s]?|repuesto[s]?|servicio[s]?)'
    match = re.search(patron_lista, consulta_lower)
    if match:
        entidad_texto = match.group(1)
        # Mapear el texto a la entidad
        if any(kw in entidad_texto for kw in ['orden']):
            return 'ordenes'
        elif 'cliente' in entidad_texto:
            return 'clientes'
        elif any(kw in entidad_texto for kw in ['vehiculo', 'vehículo', 'auto']):
            return 'vehiculos'
        elif any(kw in entidad_texto for kw in ['item', 'repuesto', 'servicio']):
            return 'items'
    
    # Si no hay patrón específico, buscar la primera coincidencia
    for entidad_id, keywords in KEYWORDS_ENTIDADES.items():
        for keyword in keywords:
            if keyword in consulta_lower:
                return entidad_id
    
    return None


def extraer_fechas(consulta):
    """
    Extrae rangos de fechas de la consulta
    
    Args:
        consulta: String con la consulta
    
    Returns:
        Dict con fecha_desde y fecha_hasta si se encuentran
    """
    fechas = {}
    consulta_lower = consulta.lower()
    now = timezone.now()
    
    # Este mes
    if 'este mes' in consulta_lower:
        fecha_desde = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        fecha_hasta = now
        fechas['fecha_desde'] = fecha_desde
        fechas['fecha_hasta'] = fecha_hasta
        return fechas
    
    # Este año
    if 'este año' in consulta_lower or 'este ano' in consulta_lower:
        fecha_desde = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        fecha_hasta = now
        fechas['fecha_desde'] = fecha_desde
        fechas['fecha_hasta'] = fecha_hasta
        return fechas
    
    # Hoy
    if 'hoy' in consulta_lower:
        fecha_desde = now.replace(hour=0, minute=0, second=0, microsecond=0)
        fecha_hasta = now
        fechas['fecha_desde'] = fecha_desde
        fechas['fecha_hasta'] = fecha_hasta
        return fechas
    
    # Ayer
    if 'ayer' in consulta_lower:
        ayer = now - timedelta(days=1)
        fecha_desde = ayer.replace(hour=0, minute=0, second=0, microsecond=0)
        fecha_hasta = ayer.replace(hour=23, minute=59, second=59)
        fechas['fecha_desde'] = fecha_desde
        fechas['fecha_hasta'] = fecha_hasta
        return fechas
    
    # Esta semana
    if 'esta semana' in consulta_lower:
        fecha_desde = now - timedelta(days=now.weekday())
        fecha_hasta = now
        fechas['fecha_desde'] = fecha_desde
        fechas['fecha_hasta'] = fecha_hasta
        return fechas
    
    # Último mes / mes pasado
    if 'último mes' in consulta_lower or 'ultimo mes' in consulta_lower or 'mes pasado' in consulta_lower:
        primer_dia_mes_actual = now.replace(day=1)
        ultimo_dia_mes_pasado = primer_dia_mes_actual - timedelta(days=1)
        primer_dia_mes_pasado = ultimo_dia_mes_pasado.replace(day=1)
        fechas['fecha_desde'] = primer_dia_mes_pasado
        fechas['fecha_hasta'] = ultimo_dia_mes_pasado
        return fechas
    
    # Últimos X días
    match_dias = re.search(r'últimos? (\d+) días?|ultimos? (\d+) dias?', consulta_lower)
    if match_dias:
        dias = int(match_dias.group(1) or match_dias.group(2))
        fecha_desde = now - timedelta(days=dias)
        fecha_hasta = now
        fechas['fecha_desde'] = fecha_desde
        fechas['fecha_hasta'] = fecha_hasta
        return fechas
    
    # Últimas X semanas
    match_semanas = re.search(r'últimas? (\d+) semanas?|ultimas? (\d+) semanas?', consulta_lower)
    if match_semanas:
        semanas = int(match_semanas.group(1) or match_semanas.group(2))
        fecha_desde = now - timedelta(weeks=semanas)
        fecha_hasta = now
        fechas['fecha_desde'] = fecha_desde
        fechas['fecha_hasta'] = fecha_hasta
        return fechas
    
    # Buscar meses específicos (enero, febrero, etc.)
    meses = {
        'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
        'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
        'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
    }
    
    for mes_nombre, mes_num in meses.items():
        if mes_nombre in consulta_lower:
            # Extraer año si está presente
            year_match = re.search(r'\b(20\d{2})\b', consulta)
            year = int(year_match.group(1)) if year_match else timezone.now().year
            
            fecha_inicio = timezone.datetime(year, mes_num, 1)
            if mes_num == 12:
                fecha_fin = timezone.datetime(year + 1, 1, 1) - timedelta(seconds=1)
            else:
                fecha_fin = timezone.datetime(year, mes_num + 1, 1) - timedelta(seconds=1)
            
            fechas['fecha_desde'] = timezone.make_aware(fecha_inicio)
            fechas['fecha_hasta'] = timezone.make_aware(fecha_fin)
            return fechas
    
    # Intentar parsear fechas absolutas con dateparser
    fecha_desde_match = re.search(r'desde (\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', consulta_lower)
    fecha_hasta_match = re.search(r'hasta (\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', consulta_lower)
    
    if fecha_desde_match:
        fecha_desde = dateparser.parse(fecha_desde_match.group(1), languages=['es'])
        if fecha_desde:
            fechas['fecha_desde'] = timezone.make_aware(fecha_desde) if timezone.is_naive(fecha_desde) else fecha_desde
    
    if fecha_hasta_match:
        fecha_hasta = dateparser.parse(fecha_hasta_match.group(1), languages=['es'])
        if fecha_hasta:
            fechas['fecha_hasta'] = timezone.make_aware(fecha_hasta) if timezone.is_naive(fecha_hasta) else fecha_hasta
    
    return fechas


def extraer_estado_orden(consulta):
    """
    Extrae el estado de orden de la consulta
    
    Args:
        consulta: String con la consulta
    
    Returns:
        String con el estado o None
    """
    consulta_lower = consulta.lower()
    
    for estado_key, keywords in ESTADOS_ORDENES.items():
        for keyword in keywords:
            if keyword in consulta_lower:
                return estado_key
    
    return None


def extraer_tipo_item(consulta):
    """
    Extrae el tipo de item de la consulta
    
    Args:
        consulta: String con la consulta
    
    Returns:
        String con el tipo o None
    """
    consulta_lower = consulta.lower()
    
    for tipo_key, keywords in TIPOS_ITEMS.items():
        for keyword in keywords:
            if keyword in consulta_lower:
                return tipo_key
    
    return None


def extraer_comparacion_numerica(consulta, campo_base):
    """
    Extrae comparaciones numéricas (mayor que, menor que, etc.)
    
    Args:
        consulta: String con la consulta
        campo_base: String con el nombre del campo (total, stock, precio, etc.)
    
    Returns:
        Dict con los filtros numéricos
    """
    filtros = {}
    consulta_lower = consulta.lower()
    
    # Patrones para extraer números
    patrones = [
        (rf'{campo_base}\s+mayor\s+(?:a|que|de)\s+(\d+(?:\.\d+)?)', f'{campo_base}__gt'),
        (rf'{campo_base}\s+menor\s+(?:a|que|de)\s+(\d+(?:\.\d+)?)', f'{campo_base}__lt'),
        (rf'{campo_base}\s+igual\s+(?:a|que)\s+(\d+(?:\.\d+)?)', campo_base),
        (rf'mayor\s+(?:a|que|de)\s+(\d+(?:\.\d+)?)', f'{campo_base}__gt'),
        (rf'menor\s+(?:a|que|de)\s+(\d+(?:\.\d+)?)', f'{campo_base}__lt'),
        (rf'más\s+de\s+(\d+(?:\.\d+)?)', f'{campo_base}__gt'),
        (rf'menos\s+de\s+(\d+(?:\.\d+)?)', f'{campo_base}__lt'),
    ]
    
    for patron, filtro_key in patrones:
        match = re.search(patron, consulta_lower)
        if match:
            valor = float(match.group(1))
            filtros[filtro_key] = valor
            break
    
    return filtros


def extraer_stock_bajo(consulta):
    """
    Detecta si se solicitan items con stock bajo/crítico
    
    Args:
        consulta: String con la consulta
    
    Returns:
        Bool indicando si se debe filtrar por stock bajo
    """
    consulta_lower = consulta.lower()
    keywords_stock_bajo = ['stock bajo', 'stock crítico', 'stock critico', 'poco stock', 'sin stock']
    
    return any(keyword in consulta_lower for keyword in keywords_stock_bajo)


def extraer_busqueda_texto(consulta, entidad):
    """
    Extrae búsquedas de texto (nombre contiene, placa contiene, etc.)
    
    Args:
        consulta: String con la consulta
        entidad: String con el ID de la entidad
    
    Returns:
        Dict con filtros de texto
    """
    filtros = {}
    consulta_lower = consulta.lower()
    
    # Patrones comunes
    patrones = {
        'ordenes': [
            (r'cliente\s+(?:llamado|con nombre|de nombre)\s+["\']?([^"\']+)["\']?', 'cliente__nombre__icontains'),
            (r'placa\s+["\']?([A-Z0-9-]+)["\']?', 'vehiculo__numero_placa__icontains'),
        ],
        'clientes': [
            (r'nombre\s+(?:llamado|con nombre|de nombre)\s+["\']?([^"\']+)["\']?', 'nombre__icontains'),
            (r'apellido\s+["\']?([^"\']+)["\']?', 'apellido__icontains'),
        ],
        'vehiculos': [
            (r'marca\s+["\']?([^"\']+)["\']?', 'marca__nombre__icontains'),
            (r'modelo\s+["\']?([^"\']+)["\']?', 'modelo__nombre__icontains'),
            (r'placa\s+["\']?([A-Z0-9-]+)["\']?', 'numero_placa__icontains'),
            (r'color\s+["\']?([^"\']+)["\']?', 'color__icontains'),
        ],
        'items': [
            (r'nombre\s+["\']?([^"\']+)["\']?', 'nombre__icontains'),
            (r'fabricante\s+["\']?([^"\']+)["\']?', 'fabricante__icontains'),
        ],
    }
    
    if entidad in patrones:
        for patron, filtro_key in patrones[entidad]:
            match = re.search(patron, consulta_lower)
            if match:
                filtros[filtro_key] = match.group(1).strip()
    
    return filtros


def interpretar_consulta(consulta):
    """
    Función principal que interpreta una consulta en lenguaje natural
    
    Args:
        consulta: String con la consulta del usuario
    
    Returns:
        Dict con:
        - entidad: ID de la entidad
        - filtros: Dict de filtros a aplicar
        - campos_sugeridos: Lista de campos relevantes
        - error: String con mensaje de error si no se puede interpretar
    """
    resultado = {
        'entidad': None,
        'filtros': {},
        'campos_sugeridos': [],
        'consulta_original': consulta,
        'error': None
    }
    
    # 1. Detectar entidad
    entidad = detectar_entidad(consulta)
    if not entidad:
        resultado['error'] = 'No se pudo identificar la entidad (órdenes, clientes, vehículos o items)'
        return resultado
    
    resultado['entidad'] = entidad
    config_entidad = ENTIDADES_DISPONIBLES[entidad]
    
    # 2. Extraer fechas si aplica
    if entidad in ['ordenes', 'clientes']:
        fechas = extraer_fechas(consulta)
        
        if entidad == 'ordenes':
            if fechas.get('fecha_desde'):
                resultado['filtros']['fecha_creacion__gte'] = fechas['fecha_desde'].strftime('%Y-%m-%d')
            if fechas.get('fecha_hasta'):
                resultado['filtros']['fecha_creacion__lte'] = fechas['fecha_hasta'].strftime('%Y-%m-%d')
        elif entidad == 'clientes':
            if fechas.get('fecha_desde'):
                resultado['filtros']['created_at__gte'] = fechas['fecha_desde'].strftime('%Y-%m-%d')
            if fechas.get('fecha_hasta'):
                resultado['filtros']['created_at__lte'] = fechas['fecha_hasta'].strftime('%Y-%m-%d')
    
    # 3. Filtros específicos por entidad
    if entidad == 'ordenes':
        # Estado
        estado = extraer_estado_orden(consulta)
        if estado:
            resultado['filtros']['estado'] = estado
        
        # Total
        filtros_total = extraer_comparacion_numerica(consulta, 'total')
        resultado['filtros'].update(filtros_total)
        
        # Campos sugeridos
        resultado['campos_sugeridos'] = [
            'id', 'fecha_creacion', 'estado', 'fallo_requerimiento', 'total',
            'cliente__nombre', 'cliente__apellido', 'vehiculo__numero_placa'
        ]
    
    elif entidad == 'clientes':
        # Tipo de cliente
        if 'empresa' in consulta.lower():
            resultado['filtros']['tipo_cliente'] = 'EMPRESA'
        elif 'natural' in consulta.lower() or 'persona' in consulta.lower():
            resultado['filtros']['tipo_cliente'] = 'NATURAL'
        
        # Campos sugeridos
        resultado['campos_sugeridos'] = [
            'id', 'nombre', 'apellido', 'nit', 'telefono', 'email', 'tipo_cliente', 'created_at'
        ]
    
    elif entidad == 'vehiculos':
        # Año
        filtros_año = extraer_comparacion_numerica(consulta, 'año')
        resultado['filtros'].update(filtros_año)
        
        # Campos sugeridos
        resultado['campos_sugeridos'] = [
            'id', 'numero_placa', 'marca__nombre', 'modelo__nombre', 'año', 
            'color', 'tipo', 'cliente__nombre'
        ]
    
    elif entidad == 'items':
        # Tipo de item
        tipo_item = extraer_tipo_item(consulta)
        if tipo_item:
            resultado['filtros']['tipo'] = tipo_item
        
        # Stock bajo
        if extraer_stock_bajo(consulta):
            # Filtrar items donde stock < 10 o donde stock es menor al stock_minimo si existiera
            resultado['filtros']['stock__lt'] = 10
        
        # Stock comparación
        filtros_stock = extraer_comparacion_numerica(consulta, 'stock')
        resultado['filtros'].update(filtros_stock)
        
        # Precio comparación
        filtros_precio = extraer_comparacion_numerica(consulta, 'precio')
        resultado['filtros'].update(filtros_precio)
        
        # Costo comparación
        filtros_costo = extraer_comparacion_numerica(consulta, 'costo')
        resultado['filtros'].update(filtros_costo)
        
        # Estado
        if 'disponible' in consulta.lower() and 'no disponible' not in consulta.lower():
            resultado['filtros']['estado'] = 'Disponible'
        elif 'no disponible' in consulta.lower():
            resultado['filtros']['estado'] = 'No disponible'
        
        # Campos sugeridos
        resultado['campos_sugeridos'] = [
            'id', 'codigo', 'nombre', 'tipo', 'fabricante', 'precio', 'costo', 'stock', 'estado'
        ]
    
    # 4. Extraer búsquedas de texto
    filtros_texto = extraer_busqueda_texto(consulta, entidad)
    resultado['filtros'].update(filtros_texto)
    
    # 5. Validar que los filtros estén en la whitelist
    filtros_validos = {}
    filtros_disponibles = set(config_entidad['filtros_disponibles'].keys())
    
    for filtro_key, filtro_valor in resultado['filtros'].items():
        if filtro_key in filtros_disponibles:
            filtros_validos[filtro_key] = filtro_valor
    
    resultado['filtros'] = filtros_validos
    
    return resultado


def generar_ejemplos_consultas():
    """
    Genera ejemplos de consultas que el sistema puede interpretar
    
    Returns:
        Dict con ejemplos por entidad
    """
    return {
        'ordenes': [
            "Órdenes completadas este mes",
            "Órdenes pendientes con total mayor a 1000",
            "Órdenes en proceso de este año",
            "Órdenes del cliente Juan",
            "Órdenes terminadas en octubre",
        ],
        'clientes': [
            "Clientes registrados en octubre",
            "Clientes tipo empresa",
            "Todos los clientes registrados este mes",
            "Clientes persona natural",
        ],
        'vehiculos': [
            "Vehículos marca Toyota",
            "Vehículos año mayor a 2015",
            "Autos modelo Corolla",
            "Vehículos color blanco",
        ],
        'items': [
            "Items con stock bajo",
            "Repuestos de venta disponibles",
            "Servicios disponibles",
            "Items con precio mayor a 100",
            "Repuestos con stock menor a 5",
        ]
    }
