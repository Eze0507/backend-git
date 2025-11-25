"""
Parser de Lenguaje Natural para Reportes
Interpreta consultas en español y las convierte en filtros de base de datos
Soporta múltiples entidades: órdenes, clientes, vehículos, items, citas, presupuestos, 
facturas de proveedores, empleados, pagos, áreas y proveedores
"""
import re
import dateparser
from datetime import datetime, timedelta
from django.utils import timezone
from .whitelist import ENTIDADES_DISPONIBLES


# Mapeo de palabras clave a entidades (expandido)
KEYWORDS_ENTIDADES = {
    'ordenes': ['orden', 'ordenes', 'órdenes', 'trabajo', 'trabajos', 'ot', 'reparacion', 'reparación'],
    'clientes': ['cliente', 'clientes'],
    'vehiculos': ['vehiculo', 'vehiculos', 'vehículo', 'vehículos', 'auto', 'autos', 'carro', 'carros', 'moto', 'motos'],
    'items': ['item', 'items', 'repuesto', 'repuestos', 'producto', 'productos', 'pieza', 'piezas', 'inventario'],
    'citas': ['cita', 'citas', 'agendamiento', 'agenda', 'turno', 'turnos', 'reserva', 'reservas'],
    'presupuestos': ['presupuesto', 'presupuestos', 'cotizacion', 'cotizaciones', 'cotización', 'cotizaciones'],
    'facturas_proveedor': ['factura proveedor', 'facturas proveedor', 'factura de proveedor', 'facturas de proveedores', 'compra', 'compras'],
    'empleados': ['empleado', 'empleados', 'trabajador', 'trabajadores', 'tecnico', 'técnico', 'tecnicos', 'técnicos', 'personal'],
    'pagos': ['pago', 'pagos', 'cobro', 'cobros', 'transaccion', 'transacción', 'transacciones'],
    'proveedores': ['proveedor', 'proveedores', 'suministrador', 'suministradores'],
    'areas': ['area', 'areas', 'área', 'áreas', 'departamento', 'departamentos', 'seccion', 'sección'],
}

# Mapeo de estados para órdenes de trabajo
ESTADOS_ORDENES = {
    'pendiente': ['pendiente', 'pendientes', 'sin comenzar', 'no iniciada', 'no iniciadas', 'no iniciado', 'no iniciados'],
    'en_proceso': ['en proceso', 'en progreso', 'trabajando', 'en curso', 'activa', 'activas', 'activo', 'activos'],
    'finalizada': ['finalizada', 'finalizadas', 'finalizado', 'finalizados', 'completada', 'completadas', 'completado', 'completados', 'terminada', 'terminadas', 'terminado', 'terminados', 'acabada', 'acabadas', 'acabado', 'acabados'],
    'entregada': ['entregada', 'entregadas', 'entregado', 'entregados', 'despachada', 'despachadas', 'despachado', 'despachados'],
    'cancelada': ['cancelada', 'canceladas', 'cancelado', 'cancelados', 'anulada', 'anuladas', 'anulado', 'anulados'],
}

# Mapeo de estados para citas
ESTADOS_CITAS = {
    'pendiente': ['pendiente', 'pendientes', 'por confirmar'],
    'confirmada': ['confirmada', 'confirmadas', 'confirmado', 'confirmados', 'aceptada', 'aceptadas', 'aceptado', 'aceptados'],
    'cancelada': ['cancelada', 'canceladas', 'cancelado', 'cancelados', 'anulada', 'anuladas', 'anulado', 'anulados'],
    'completada': ['completada', 'completadas', 'completado', 'completados', 'realizada', 'realizadas', 'realizado', 'realizados', 'cumplida', 'cumplidas', 'cumplido', 'cumplidos'],
}

# Mapeo de tipos de cita
TIPOS_CITA = {
    'reparacion': ['reparacion', 'reparación', 'arreglo'],
    'mantenimiento': ['mantenimiento', 'mantención', 'revision', 'revisión'],
    'diagnostico': ['diagnostico', 'diagnóstico', 'evaluacion', 'evaluación', 'inspeccion', 'inspección'],
    'entrega': ['entrega', 'despacho', 'retiro'],
}

# Mapeo de estados para presupuestos
ESTADOS_PRESUPUESTOS = {
    'pendiente': ['pendiente', 'pendientes', 'en espera'],
    'aprobado': ['aprobado', 'aprobados', 'aprobada', 'aprobadas', 'aceptado', 'aceptados', 'aceptada', 'aceptadas'],
    'rechazado': ['rechazado', 'rechazados', 'rechazada', 'rechazadas', 'denegado', 'denegados', 'denegada', 'denegadas', 'negado', 'negados', 'negada', 'negadas'],
    'cancelado': ['cancelado', 'cancelados', 'cancelada', 'canceladas', 'anulado', 'anulados', 'anulada', 'anuladas'],
}

# Mapeo de estados para pagos
ESTADOS_PAGOS = {
    'pendiente': ['pendiente', 'pendientes', 'sin pagar', 'por pagar'],
    'procesando': ['procesando', 'en proceso', 'en curso'],
    'completado': ['completado', 'completados', 'completada', 'completadas', 'pagado', 'pagados', 'pagada', 'pagadas', 'exitoso', 'exitosos', 'exitosa', 'exitosas'],
    'fallido': ['fallido', 'fallidos', 'fallida', 'fallidas', 'rechazado', 'rechazados', 'rechazada', 'rechazadas', 'error', 'errores'],
    'reembolsado': ['reembolsado', 'reembolsados', 'reembolsada', 'reembolsadas', 'devuelto', 'devueltos', 'devuelta', 'devueltas'],
    'cancelado': ['cancelado', 'cancelados', 'cancelada', 'canceladas', 'anulado', 'anulados', 'anulada', 'anuladas'],
}

# Mapeo de métodos de pago
METODOS_PAGO = {
    'efectivo': ['efectivo', 'cash', 'dinero en efectivo'],
    'tarjeta': ['tarjeta', 'tarjetas', 'debito', 'débito', 'credito', 'crédito'],
    'transferencia': ['transferencia', 'transferencias', 'banco', 'bancaria', 'deposito', 'depósito'],
    'stripe': ['stripe', 'en linea', 'en línea', 'online'],
    'otro': ['otro', 'otros'],
}

# Mapeo de tipos de items
TIPOS_ITEMS = {
    'Item de venta': ['venta', 'ventas', 'para vender', 'comercializar'],
    'Item de taller': ['taller', 'uso interno', 'herramienta', 'herramientas', 'interno'],
    'Servicio': ['servicio', 'servicios', 'mano de obra'],
}

# Mapeo de estados de items
ESTADOS_ITEMS = {
    'Disponible': ['disponible', 'disponibles', 'en stock', 'activo', 'activos'],
    'No disponible': ['no disponible', 'agotado', 'sin stock', 'inactivo', 'inactivos'],
}

# Mapeo de tipos de cliente
TIPOS_CLIENTE = {
    'NATURAL': ['natural', 'persona', 'individual', 'fisica', 'física'],
    'EMPRESA': ['empresa', 'compañia', 'compañía', 'corporacion', 'corporación', 'juridica', 'jurídica', 'negocio'],
}

# Mapeo de tipos de vehículo
TIPOS_VEHICULO = {
    'CAMIONETA': ['camioneta', 'camionetas', 'pickup', 'pick-up'],
    'DEPORTIVO': ['deportivo', 'deportivos', 'sport'],
    'FURGON': ['furgon', 'furgón', 'furgones', 'van'],
    'HATCHBACK': ['hatchback', 'compacto'],
    'SEDAN': ['sedan', 'sedán', 'sedanes'],
    'SUV': ['suv', 'todoterreno', 'todo terreno', '4x4'],
    'CITYCAR': ['citycar', 'city car', 'urbano'],
}

# Mapeo de sexo para empleados
SEXO_EMPLEADO = {
    'M': ['masculino', 'hombre', 'varon', 'varón', 'macho'],
    'F': ['femenino', 'mujer', 'hembra'],
    'O': ['otro', 'otros', 'no binario', 'prefiero no decir'],
}

# Mapeo de comparadores numéricos
COMPARADORES = {
    'mayor': ['mayor', 'más', 'mas', 'superior', 'arriba', 'sobre', 'encima'],
    'menor': ['menor', 'menos', 'inferior', 'abajo', 'debajo'],
    'igual': ['igual', 'exacto', 'exactamente', 'justo'],
    'entre': ['entre', 'rango', 'desde', 'hasta'],
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
    patron_lista = r'(?:dame|muestra|lista|reporte|reportes?|ver|mostrar|obtener|buscar)\s+(?:de\s+)?(?:los?\s+|las?\s+)?(orden[e]?s?|cliente[s]?|vehiculo[s]?|vehículo[s]?|auto[s]?|item[s]?|repuesto[s]?|servicio[s]?|cita[s]?|presupuesto[s]?|factura[s]?|empleado[s]?|tecnico[s]?|técnico[s]?|pago[s]?|proveedor[e]?s?|area[s]?|área[s]?)'
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
        elif 'cita' in entidad_texto:
            return 'citas'
        elif 'presupuesto' in entidad_texto:
            return 'presupuestos'
        elif 'factura' in entidad_texto:
            return 'facturas_proveedor'
        elif any(kw in entidad_texto for kw in ['empleado', 'tecnico', 'técnico']):
            return 'empleados'
        elif 'pago' in entidad_texto:
            return 'pagos'
        elif 'proveedor' in entidad_texto:
            return 'proveedores'
        elif any(kw in entidad_texto for kw in ['area', 'área']):
            return 'areas'
    
    # Si no hay patrón específico, buscar la primera coincidencia por peso
    # (más específico primero para evitar falsos positivos)
    entidades_ordenadas = ['facturas_proveedor', 'citas', 'presupuestos', 'pagos', 
                           'empleados', 'proveedores', 'areas', 'ordenes', 
                           'clientes', 'vehiculos', 'items']
    
    for entidad_id in entidades_ordenadas:
        keywords = KEYWORDS_ENTIDADES.get(entidad_id, [])
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


def extraer_estado_cita(consulta):
    """
    Extrae el estado de cita de la consulta
    
    Args:
        consulta: String con la consulta
    
    Returns:
        String con el estado o None
    """
    consulta_lower = consulta.lower()
    
    for estado_key, keywords in ESTADOS_CITAS.items():
        for keyword in keywords:
            if keyword in consulta_lower:
                return estado_key
    
    return None


def extraer_tipo_cita(consulta):
    """
    Extrae el tipo de cita de la consulta
    
    Args:
        consulta: String con la consulta
    
    Returns:
        String con el tipo o None
    """
    consulta_lower = consulta.lower()
    
    for tipo_key, keywords in TIPOS_CITA.items():
        for keyword in keywords:
            if keyword in consulta_lower:
                return tipo_key
    
    return None


def extraer_estado_presupuesto(consulta):
    """
    Extrae el estado de presupuesto de la consulta
    
    Args:
        consulta: String con la consulta
    
    Returns:
        String con el estado o None
    """
    consulta_lower = consulta.lower()
    
    for estado_key, keywords in ESTADOS_PRESUPUESTOS.items():
        for keyword in keywords:
            if keyword in consulta_lower:
                return estado_key
    
    return None


def extraer_estado_pago(consulta):
    """
    Extrae el estado de pago de la consulta
    
    Args:
        consulta: String con la consulta
    
    Returns:
        String con el estado o None
    """
    consulta_lower = consulta.lower()
    
    for estado_key, keywords in ESTADOS_PAGOS.items():
        for keyword in keywords:
            if keyword in consulta_lower:
                return estado_key
    
    return None


def extraer_metodo_pago(consulta):
    """
    Extrae el método de pago de la consulta
    
    Args:
        consulta: String con la consulta
    
    Returns:
        String con el método o None
    """
    consulta_lower = consulta.lower()
    
    for metodo_key, keywords in METODOS_PAGO.items():
        for keyword in keywords:
            if keyword in consulta_lower:
                return metodo_key
    
    return None


def extraer_tipo_cliente(consulta):
    """
    Extrae el tipo de cliente de la consulta
    
    Args:
        consulta: String con la consulta
    
    Returns:
        String con el tipo o None
    """
    consulta_lower = consulta.lower()
    
    for tipo_key, keywords in TIPOS_CLIENTE.items():
        for keyword in keywords:
            if keyword in consulta_lower:
                return tipo_key
    
    return None


def extraer_tipo_vehiculo(consulta):
    """
    Extrae el tipo de vehículo de la consulta
    
    Args:
        consulta: String con la consulta
    
    Returns:
        String con el tipo o None
    """
    consulta_lower = consulta.lower()
    
    for tipo_key, keywords in TIPOS_VEHICULO.items():
        for keyword in keywords:
            if keyword in consulta_lower:
                return tipo_key
    
    return None


def extraer_sexo_empleado(consulta):
    """
    Extrae el sexo del empleado de la consulta
    
    Args:
        consulta: String con la consulta
    
    Returns:
        String con el sexo o None
    """
    consulta_lower = consulta.lower()
    
    for sexo_key, keywords in SEXO_EMPLEADO.items():
        for keyword in keywords:
            if keyword in consulta_lower:
                return sexo_key
    
    return None


def extraer_estado_item(consulta):
    """
    Extrae el estado de item de la consulta
    
    Args:
        consulta: String con la consulta
    
    Returns:
        String con el estado o None
    """
    consulta_lower = consulta.lower()
    
    for estado_key, keywords in ESTADOS_ITEMS.items():
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
    
    # Patrones comunes por entidad
    patrones = {
        'ordenes': [
            (r'cliente\s+(?:llamado|con nombre|de nombre)\s+["\']?([^"\']+)["\']?', 'cliente__nombre__icontains'),
            (r'placa\s+["\']?([A-Z0-9-]+)["\']?', 'vehiculo__numero_placa__icontains'),
            (r'fallo\s+["\']?([^"\']+)["\']?', 'fallo_requerimiento__icontains'),
        ],
        'clientes': [
            (r'nombre\s+(?:llamado|con nombre|de nombre)\s+["\']?([^"\']+)["\']?', 'nombre__icontains'),
            (r'apellido\s+["\']?([^"\']+)["\']?', 'apellido__icontains'),
            (r'nit\s+["\']?([0-9-]+)["\']?', 'nit__icontains'),
            (r'telefono\s+["\']?([0-9-]+)["\']?', 'telefono__icontains'),
        ],
        'vehiculos': [
            (r'marca\s+["\']?([^"\']+)["\']?', 'marca__nombre__icontains'),
            (r'modelo\s+["\']?([^"\']+)["\']?', 'modelo__nombre__icontains'),
            (r'placa\s+["\']?([A-Z0-9-]+)["\']?', 'numero_placa__icontains'),
            (r'color\s+["\']?([^"\']+)["\']?', 'color__icontains'),
            (r'vin\s+["\']?([A-Z0-9-]+)["\']?', 'vin__icontains'),
        ],
        'items': [
            (r'nombre\s+["\']?([^"\']+)["\']?', 'nombre__icontains'),
            (r'codigo\s+["\']?([A-Z0-9-]+)["\']?', 'codigo__icontains'),
            (r'fabricante\s+["\']?([^"\']+)["\']?', 'fabricante__icontains'),
        ],
        'citas': [
            (r'cliente\s+(?:llamado|con nombre|de nombre)\s+["\']?([^"\']+)["\']?', 'cliente__nombre__icontains'),
            (r'empleado\s+(?:llamado|con nombre|de nombre)\s+["\']?([^"\']+)["\']?', 'empleado__nombre__icontains'),
            (r'placa\s+["\']?([A-Z0-9-]+)["\']?', 'vehiculo__numero_placa__icontains'),
        ],
        'presupuestos': [
            (r'cliente\s+(?:llamado|con nombre|de nombre)\s+["\']?([^"\']+)["\']?', 'cliente__nombre__icontains'),
            (r'placa\s+["\']?([A-Z0-9-]+)["\']?', 'vehiculo__numero_placa__icontains'),
            (r'diagnostico\s+["\']?([^"\']+)["\']?', 'diagnostico__icontains'),
        ],
        'facturas_proveedor': [
            (r'numero\s+["\']?([A-Z0-9-]+)["\']?', 'numero__icontains'),
            (r'proveedor\s+(?:llamado|con nombre|de nombre)\s+["\']?([^"\']+)["\']?', 'proveedor__nombre__icontains'),
        ],
        'empleados': [
            (r'nombre\s+(?:llamado|con nombre|de nombre)\s+["\']?([^"\']+)["\']?', 'nombre__icontains'),
            (r'apellido\s+["\']?([^"\']+)["\']?', 'apellido__icontains'),
            (r'ci\s+["\']?([0-9-]+)["\']?', 'ci__icontains'),
            (r'cargo\s+["\']?([^"\']+)["\']?', 'cargo__nombre__icontains'),
            (r'area\s+["\']?([^"\']+)["\']?', 'area__nombre__icontains'),
        ],
        'pagos': [
            (r'referencia\s+["\']?([A-Z0-9-]+)["\']?', 'numero_referencia__icontains'),
            (r'orden\s+(?:numero|#)?\s*(\d+)', 'orden_trabajo__id'),
        ],
        'proveedores': [
            (r'nombre\s+["\']?([^"\']+)["\']?', 'nombre__icontains'),
            (r'nit\s+["\']?([0-9-]+)["\']?', 'nit__icontains'),
            (r'contacto\s+["\']?([^"\']+)["\']?', 'contacto__icontains'),
        ],
        'areas': [
            (r'nombre\s+["\']?([^"\']+)["\']?', 'nombre__icontains'),
        ],
    }
    
    if entidad in patrones:
        for patron, filtro_key in patrones[entidad]:
            match = re.search(patron, consulta_lower)
            if match:
                valor = match.group(1).strip()
                # Convertir a int si el filtro es para ID
                if filtro_key.endswith('__id'):
                    try:
                        valor = int(valor)
                    except ValueError:
                        continue
                filtros[filtro_key] = valor
    
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
        - formato: Formato de salida solicitado (PDF o XLSX)
        - error: String con mensaje de error si no se puede interpretar
    """
    resultado = {
        'entidad': None,
        'filtros': {},
        'campos_sugeridos': [],
        'consulta_original': consulta,
        'formato': None,
        'error': None
    }
    
    # 0. Detectar formato solicitado y limpiar consulta
    formato = detectar_formato(consulta)
    consulta_limpia = limpiar_formato_de_consulta(consulta)
    resultado['formato'] = formato
    
    # 1. Detectar entidad
    entidad = detectar_entidad(consulta_limpia)
    if not entidad:
        resultado['error'] = 'No se pudo identificar la entidad (órdenes, clientes, vehículos o items)'
        return resultado
    
    resultado['entidad'] = entidad
    config_entidad = ENTIDADES_DISPONIBLES[entidad]
    
    # 2. Extraer fechas si aplica
    if entidad in ['ordenes', 'clientes', 'citas', 'presupuestos', 'facturas_proveedor', 'pagos', 'empleados']:
        fechas = extraer_fechas(consulta_limpia)
        
        if entidad == 'ordenes':
            if fechas.get('fecha_desde'):
                resultado['filtros']['fecha_creacion__gte'] = fechas['fecha_desde'].strftime('%Y-%m-%d')
            if fechas.get('fecha_hasta'):
                resultado['filtros']['fecha_creacion__lte'] = fechas['fecha_hasta'].strftime('%Y-%m-%d')
        elif entidad == 'clientes':
            if fechas.get('fecha_desde'):
                resultado['filtros']['fecha_registro__gte'] = fechas['fecha_desde'].strftime('%Y-%m-%d')
            if fechas.get('fecha_hasta'):
                resultado['filtros']['fecha_registro__lte'] = fechas['fecha_hasta'].strftime('%Y-%m-%d')
        elif entidad == 'citas':
            if fechas.get('fecha_desde'):
                resultado['filtros']['fecha_hora_inicio__gte'] = fechas['fecha_desde'].strftime('%Y-%m-%d')
            if fechas.get('fecha_hasta'):
                resultado['filtros']['fecha_hora_inicio__lte'] = fechas['fecha_hasta'].strftime('%Y-%m-%d')
        elif entidad == 'presupuestos':
            if fechas.get('fecha_desde'):
                resultado['filtros']['fecha_inicio__gte'] = fechas['fecha_desde'].strftime('%Y-%m-%d')
            if fechas.get('fecha_hasta'):
                resultado['filtros']['fecha_fin__lte'] = fechas['fecha_hasta'].strftime('%Y-%m-%d')
        elif entidad == 'facturas_proveedor':
            if fechas.get('fecha_desde'):
                resultado['filtros']['fecha_registro__gte'] = fechas['fecha_desde'].strftime('%Y-%m-%d')
            if fechas.get('fecha_hasta'):
                resultado['filtros']['fecha_registro__lte'] = fechas['fecha_hasta'].strftime('%Y-%m-%d')
        elif entidad == 'pagos':
            if fechas.get('fecha_desde'):
                resultado['filtros']['fecha_pago__gte'] = fechas['fecha_desde'].strftime('%Y-%m-%d')
            if fechas.get('fecha_hasta'):
                resultado['filtros']['fecha_pago__lte'] = fechas['fecha_hasta'].strftime('%Y-%m-%d')
        elif entidad == 'empleados':
            if fechas.get('fecha_desde'):
                resultado['filtros']['fecha_registro__gte'] = fechas['fecha_desde'].strftime('%Y-%m-%d')
            if fechas.get('fecha_hasta'):
                resultado['filtros']['fecha_registro__lte'] = fechas['fecha_hasta'].strftime('%Y-%m-%d')
    
    # 3. Filtros específicos por entidad
    if entidad == 'ordenes':
        # Estado
        estado = extraer_estado_orden(consulta_limpia)
        if estado:
            resultado['filtros']['estado'] = estado
        
        # Pago
        if any(kw in consulta_limpia.lower() for kw in ['pagada', 'pagadas', 'con pago', 'cobrada', 'cobradas']):
            resultado['filtros']['pago'] = True
        elif any(kw in consulta_limpia.lower() for kw in ['sin pagar', 'pendiente pago', 'no pagada', 'no pagadas']):
            resultado['filtros']['pago'] = False
        
        # Total
        filtros_total = extraer_comparacion_numerica(consulta_limpia, 'total')
        resultado['filtros'].update(filtros_total)
        
        # Kilometraje
        filtros_kilometraje = extraer_comparacion_numerica(consulta_limpia, 'kilometraje')
        resultado['filtros'].update(filtros_kilometraje)
        
        # Campos sugeridos
        resultado['campos_sugeridos'] = [
            'id', 'fecha_creacion', 'fecha_inicio', 'fecha_finalizacion', 'estado', 
            'fallo_requerimiento', 'kilometraje', 'subtotal', 'descuento', 'impuesto', 'total', 'pago',
            'cliente__nombre', 'cliente__apellido', 'vehiculo__numero_placa', 'vehiculo__marca__nombre'
        ]
    
    elif entidad == 'clientes':
        # Tipo de cliente
        tipo_cliente = extraer_tipo_cliente(consulta_limpia)
        if tipo_cliente:
            resultado['filtros']['tipo_cliente'] = tipo_cliente
        
        # Estado activo
        if any(kw in consulta_limpia.lower() for kw in ['activo', 'activos', 'habilitado', 'habilitados']):
            resultado['filtros']['activo'] = True
        elif any(kw in consulta_limpia.lower() for kw in ['inactivo', 'inactivos', 'deshabilitado', 'deshabilitados']):
            resultado['filtros']['activo'] = False
        
        # Campos sugeridos
        resultado['campos_sugeridos'] = [
            'id', 'nombre', 'apellido', 'nit', 'telefono', 'direccion', 'tipo_cliente', 
            'activo', 'fecha_registro', 'fecha_actualizacion'
        ]
    
    elif entidad == 'vehiculos':
        # Tipo de vehículo
        tipo_vehiculo = extraer_tipo_vehiculo(consulta_limpia)
        if tipo_vehiculo:
            resultado['filtros']['tipo'] = tipo_vehiculo
        
        # Año
        filtros_año = extraer_comparacion_numerica(consulta_limpia, 'año')
        resultado['filtros'].update(filtros_año)
        
        # Cilindrada
        filtros_cilindrada = extraer_comparacion_numerica(consulta_limpia, 'cilindrada')
        resultado['filtros'].update(filtros_cilindrada)
        
        # Campos sugeridos
        resultado['campos_sugeridos'] = [
            'id', 'numero_placa', 'marca__nombre', 'modelo__nombre', 'año', 
            'color', 'tipo', 'vin', 'cilindrada', 'tipo_combustible',
            'cliente__nombre', 'cliente__apellido'
        ]
    
    elif entidad == 'items':
        # Tipo de item
        tipo_item = extraer_tipo_item(consulta_limpia)
        if tipo_item:
            resultado['filtros']['tipo'] = tipo_item
        
        # Estado
        estado_item = extraer_estado_item(consulta_limpia)
        if estado_item:
            resultado['filtros']['estado'] = estado_item
        
        # Stock bajo
        if extraer_stock_bajo(consulta_limpia):
            resultado['filtros']['stock__lt'] = 10
        
        # Stock comparación
        filtros_stock = extraer_comparacion_numerica(consulta_limpia, 'stock')
        resultado['filtros'].update(filtros_stock)
        
        # Precio comparación
        filtros_precio = extraer_comparacion_numerica(consulta_limpia, 'precio')
        resultado['filtros'].update(filtros_precio)
        
        # Costo comparación
        filtros_costo = extraer_comparacion_numerica(consulta_limpia, 'costo')
        resultado['filtros'].update(filtros_costo)
        
        # Campos sugeridos
        resultado['campos_sugeridos'] = [
            'id', 'codigo', 'nombre', 'descripcion', 'tipo', 'fabricante', 
            'precio', 'costo', 'stock', 'estado', 'area__nombre'
        ]
    
    elif entidad == 'citas':
        # Estado
        estado = extraer_estado_cita(consulta_limpia)
        if estado:
            resultado['filtros']['estado'] = estado
        
        # Tipo de cita
        tipo_cita = extraer_tipo_cita(consulta_limpia)
        if tipo_cita:
            resultado['filtros']['tipo_cita'] = tipo_cita
        
        # Campos sugeridos
        resultado['campos_sugeridos'] = [
            'id', 'fecha_hora_inicio', 'fecha_hora_fin', 'tipo_cita', 'estado', 
            'descripcion', 'cliente__nombre', 'cliente__apellido', 
            'vehiculo__numero_placa', 'empleado__nombre', 'empleado__apellido'
        ]
    
    elif entidad == 'presupuestos':
        # Estado
        estado = extraer_estado_presupuesto(consulta_limpia)
        if estado:
            resultado['filtros']['estado'] = estado
        
        # Con impuestos
        if any(kw in consulta_limpia.lower() for kw in ['con impuesto', 'con iva', 'con tax']):
            resultado['filtros']['con_impuestos'] = True
        elif any(kw in consulta_limpia.lower() for kw in ['sin impuesto', 'sin iva', 'sin tax']):
            resultado['filtros']['con_impuestos'] = False
        
        # Total
        filtros_total = extraer_comparacion_numerica(consulta_limpia, 'total')
        resultado['filtros'].update(filtros_total)
        
        # Campos sugeridos
        resultado['campos_sugeridos'] = [
            'id', 'fecha_inicio', 'fecha_fin', 'estado', 'diagnostico',
            'con_impuestos', 'subtotal', 'total_descuentos', 'impuestos', 'total',
            'cliente__nombre', 'cliente__apellido', 'vehiculo__numero_placa'
        ]
    
    elif entidad == 'facturas_proveedor':
        # Comparaciones numéricas
        filtros_total = extraer_comparacion_numerica(consulta_limpia, 'total')
        resultado['filtros'].update(filtros_total)
        
        filtros_subtotal = extraer_comparacion_numerica(consulta_limpia, 'subtotal')
        resultado['filtros'].update(filtros_subtotal)
        
        # Campos sugeridos
        resultado['campos_sugeridos'] = [
            'id', 'numero', 'fecha_registro', 'subtotal', 'descuento', 'impuesto', 
            'total', 'observacion', 'proveedor__nombre', 'proveedor__nit'
        ]
    
    elif entidad == 'empleados':
        # Sexo
        sexo = extraer_sexo_empleado(consulta_limpia)
        if sexo:
            resultado['filtros']['sexo'] = sexo
        
        # Estado (activo/inactivo)
        if any(kw in consulta_limpia.lower() for kw in ['activo', 'activos', 'habilitado', 'trabajando']):
            resultado['filtros']['estado'] = True
        elif any(kw in consulta_limpia.lower() for kw in ['inactivo', 'inactivos', 'deshabilitado', 'retirado']):
            resultado['filtros']['estado'] = False
        
        # Sueldo
        filtros_sueldo = extraer_comparacion_numerica(consulta_limpia, 'sueldo')
        resultado['filtros'].update(filtros_sueldo)
        
        # Campos sugeridos
        resultado['campos_sugeridos'] = [
            'id', 'nombre', 'apellido', 'ci', 'telefono', 'direccion', 'sexo',
            'sueldo', 'estado', 'fecha_registro', 'cargo__nombre', 'area__nombre'
        ]
    
    elif entidad == 'pagos':
        # Estado
        estado = extraer_estado_pago(consulta_limpia)
        if estado:
            resultado['filtros']['estado'] = estado
        
        # Método de pago
        metodo = extraer_metodo_pago(consulta_limpia)
        if metodo:
            resultado['filtros']['metodo_pago'] = metodo
        
        # Monto
        filtros_monto = extraer_comparacion_numerica(consulta_limpia, 'monto')
        resultado['filtros'].update(filtros_monto)
        
        # Campos sugeridos
        resultado['campos_sugeridos'] = [
            'id', 'fecha_pago', 'monto', 'metodo_pago', 'estado', 'currency',
            'descripcion', 'numero_referencia', 'orden_trabajo__id', 
            'orden_trabajo__cliente__nombre'
        ]
    
    elif entidad == 'proveedores':
        # Campos sugeridos
        resultado['campos_sugeridos'] = [
            'id', 'nombre', 'nit', 'contacto', 'telefono', 'correo', 'direccion'
        ]
    
    elif entidad == 'areas':
        # Campos sugeridos
        resultado['campos_sugeridos'] = [
            'id', 'nombre'
        ]
    
    # 4. Extraer búsquedas de texto
    filtros_texto = extraer_busqueda_texto(consulta_limpia, entidad)
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
            "Órdenes finalizadas en octubre en excel",
            "Órdenes del cliente Juan en formato pdf",
            "Órdenes pagadas este mes",
            "Órdenes sin pagar pendientes en excel",
            "Órdenes con kilometraje mayor a 50000",
            "Órdenes entregadas esta semana como excel",
            "Órdenes canceladas en noviembre en pdf",
        ],
        'clientes': [
            "Clientes registrados en octubre",
            "Clientes tipo empresa",
            "Clientes persona natural",
            "Todos los clientes registrados este mes",
            "Clientes activos",
            "Clientes inactivos del último año",
            "Clientes empresa registrados este año",
        ],
        'vehiculos': [
            "Vehículos marca Toyota",
            "Vehículos año mayor a 2015",
            "Autos modelo Corolla",
            "Vehículos color blanco",
            "SUV año 2020 o superior",
            "Camionetas marca Nissan",
            "Vehículos tipo sedan color negro",
            "Autos con cilindrada mayor a 2000",
        ],
        'items': [
            "Items con stock bajo",
            "Repuestos de venta disponibles",
            "Servicios disponibles",
            "Items con precio mayor a 100",
            "Repuestos con stock menor a 5",
            "Items de taller disponibles",
            "Servicios con costo mayor a 200",
            "Repuestos no disponibles",
            "Items fabricante Bosch",
        ],
        'citas': [
            "Citas pendientes de esta semana",
            "Citas confirmadas de hoy",
            "Citas de mantenimiento de este mes",
            "Citas canceladas en octubre",
            "Citas de reparación pendientes",
            "Citas completadas esta semana",
            "Citas de diagnóstico confirmadas",
        ],
        'presupuestos': [
            "Presupuestos pendientes",
            "Presupuestos aprobados este mes",
            "Presupuestos rechazados en octubre",
            "Presupuestos con total mayor a 5000",
            "Presupuestos con impuestos aprobados",
            "Presupuestos del cliente María",
            "Presupuestos cancelados este año",
        ],
        'facturas_proveedor': [
            "Facturas de proveedor de este mes",
            "Facturas con total mayor a 10000",
            "Facturas del proveedor Autopartes SA",
            "Facturas registradas en octubre",
            "Facturas con descuento mayor a 500",
        ],
        'empleados': [
            "Empleados activos",
            "Empleados del área mecánica",
            "Empleados con sueldo mayor a 3000",
            "Técnicos registrados este año",
            "Empleados masculinos del cargo mecánico",
            "Personal inactivo",
        ],
        'pagos': [
            "Pagos completados este mes",
            "Pagos pendientes",
            "Pagos por stripe de esta semana",
            "Pagos en efectivo completados",
            "Pagos con monto mayor a 1000",
            "Pagos fallidos en octubre",
            "Pagos reembolsados este año",
        ],
        'proveedores': [
            "Proveedores con nombre Autopartes",
            "Proveedores con contacto Juan",
            "Todos los proveedores",
        ],
        'areas': [
            "Áreas del taller",
            "Área de nombre Mecánica",
            "Todas las áreas",
        ],
    }


def sugerir_agrupaciones(entidad):
    """
    Sugiere campos útiles para agrupar/agregar datos según la entidad
    
    Args:
        entidad: String con el ID de la entidad
    
    Returns:
        List de sugerencias de agrupación
    """
    sugerencias = {
        'ordenes': [
            {'campo': 'estado', 'label': 'Por Estado'},
            {'campo': 'cliente', 'label': 'Por Cliente'},
            {'campo': 'fecha_creacion__month', 'label': 'Por Mes'},
            {'campo': 'vehiculo__marca', 'label': 'Por Marca de Vehículo'},
            {'campo': 'pago', 'label': 'Por Estado de Pago'},
        ],
        'clientes': [
            {'campo': 'tipo_cliente', 'label': 'Por Tipo'},
            {'campo': 'fecha_registro__month', 'label': 'Por Mes de Registro'},
            {'campo': 'activo', 'label': 'Por Estado'},
        ],
        'vehiculos': [
            {'campo': 'marca', 'label': 'Por Marca'},
            {'campo': 'tipo', 'label': 'Por Tipo'},
            {'campo': 'año', 'label': 'Por Año'},
            {'campo': 'cliente', 'label': 'Por Propietario'},
        ],
        'items': [
            {'campo': 'tipo', 'label': 'Por Tipo'},
            {'campo': 'estado', 'label': 'Por Estado'},
            {'campo': 'fabricante', 'label': 'Por Fabricante'},
            {'campo': 'area', 'label': 'Por Área'},
        ],
        'citas': [
            {'campo': 'estado', 'label': 'Por Estado'},
            {'campo': 'tipo_cita', 'label': 'Por Tipo'},
            {'campo': 'empleado', 'label': 'Por Empleado'},
            {'campo': 'fecha_hora_inicio__date', 'label': 'Por Fecha'},
        ],
        'presupuestos': [
            {'campo': 'estado', 'label': 'Por Estado'},
            {'campo': 'cliente', 'label': 'Por Cliente'},
            {'campo': 'con_impuestos', 'label': 'Con/Sin Impuestos'},
        ],
        'facturas_proveedor': [
            {'campo': 'proveedor', 'label': 'Por Proveedor'},
            {'campo': 'fecha_registro__month', 'label': 'Por Mes'},
        ],
        'empleados': [
            {'campo': 'cargo', 'label': 'Por Cargo'},
            {'campo': 'area', 'label': 'Por Área'},
            {'campo': 'sexo', 'label': 'Por Sexo'},
            {'campo': 'estado', 'label': 'Por Estado'},
        ],
        'pagos': [
            {'campo': 'estado', 'label': 'Por Estado'},
            {'campo': 'metodo_pago', 'label': 'Por Método de Pago'},
            {'campo': 'fecha_pago__date', 'label': 'Por Fecha'},
        ],
    }
    
    return sugerencias.get(entidad, [])


def detectar_agregaciones(consulta):
    """
    Detecta si la consulta solicita agregaciones (contar, sumar, promediar)
    
    Args:
        consulta: String con la consulta
    
    Returns:
        Dict con información de agregación o None
    """
    consulta_lower = consulta.lower()
    
    # Contar
    if any(kw in consulta_lower for kw in ['cuantos', 'cuántos', 'cuantas', 'cuántas', 'cantidad de', 'numero de', 'número de', 'contar', 'total de']):
        return {'tipo': 'count', 'label': 'Cantidad'}
    
    # Sumar
    if any(kw in consulta_lower for kw in ['suma', 'sumar', 'total', 'totales']):
        # Detectar qué campo sumar
        if 'total' in consulta_lower or 'monto' in consulta_lower or 'precio' in consulta_lower:
            return {'tipo': 'sum', 'campo': 'total', 'label': 'Total'}
        elif 'stock' in consulta_lower:
            return {'tipo': 'sum', 'campo': 'stock', 'label': 'Stock Total'}
        elif 'sueldo' in consulta_lower:
            return {'tipo': 'sum', 'campo': 'sueldo', 'label': 'Sueldos Totales'}
    
    # Promediar
    if any(kw in consulta_lower for kw in ['promedio', 'media', 'average']):
        if 'total' in consulta_lower or 'monto' in consulta_lower or 'precio' in consulta_lower:
            return {'tipo': 'avg', 'campo': 'total', 'label': 'Promedio'}
        elif 'sueldo' in consulta_lower:
            return {'tipo': 'avg', 'campo': 'sueldo', 'label': 'Sueldo Promedio'}
    
    # Máximo/Mínimo
    if any(kw in consulta_lower for kw in ['mayor', 'maximo', 'máximo', 'max']):
        return {'tipo': 'max', 'label': 'Máximo'}
    
    if any(kw in consulta_lower for kw in ['menor', 'minimo', 'mínimo', 'min']):
        return {'tipo': 'min', 'label': 'Mínimo'}
    
    return None


def detectar_ordenamiento(consulta):
    """
    Detecta si la consulta solicita ordenamiento específico
    
    Args:
        consulta: String con la consulta
    
    Returns:
        Dict con información de ordenamiento o None
    """
    consulta_lower = consulta.lower()
    
    ordenamiento = {}
    
    # Detectar orden ascendente/descendente
    if any(kw in consulta_lower for kw in ['mas reciente', 'más reciente', 'recientes', 'ultimos', 'últimos', 'nuevos']):
        ordenamiento['direccion'] = 'desc'
    elif any(kw in consulta_lower for kw in ['mas antiguo', 'más antiguo', 'antiguos', 'viejos', 'primeros']):
        ordenamiento['direccion'] = 'asc'
    elif 'descendente' in consulta_lower or 'desc' in consulta_lower:
        ordenamiento['direccion'] = 'desc'
    elif 'ascendente' in consulta_lower or 'asc' in consulta_lower:
        ordenamiento['direccion'] = 'asc'
    
    # Detectar campo de ordenamiento
    if 'fecha' in consulta_lower:
        ordenamiento['campo'] = 'fecha_creacion'
    elif 'total' in consulta_lower or 'monto' in consulta_lower or 'precio' in consulta_lower:
        ordenamiento['campo'] = 'total'
    elif 'nombre' in consulta_lower:
        ordenamiento['campo'] = 'nombre'
    elif 'stock' in consulta_lower:
        ordenamiento['campo'] = 'stock'
    
    return ordenamiento if ordenamiento else None


def detectar_limite(consulta):
    """
    Detecta si la consulta solicita un límite de resultados
    
    Args:
        consulta: String con la consulta
    
    Returns:
        Int con el límite o None
    """
    consulta_lower = consulta.lower()
    
    # Buscar "top N", "primeros N", "últimos N"
    patrones = [
        r'top\s+(\d+)',
        r'primeros?\s+(\d+)',
        r'ultimos?\s+(\d+)',
        r'últimos?\s+(\d+)',
        r'solo\s+(\d+)',
        r'limit[e]?\s+(\d+)',
    ]
    
    for patron in patrones:
        match = re.search(patron, consulta_lower)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                continue
    
    return None


def analizar_complejidad_consulta(consulta):
    """
    Analiza la complejidad de una consulta para determinar el mejor enfoque
    
    Args:
        consulta: String con la consulta
    
    Returns:
        Dict con información de complejidad
    """
    consulta_lower = consulta.lower()
    
    complejidad = {
        'tiene_fechas': False,
        'tiene_agregaciones': False,
        'tiene_ordenamiento': False,
        'tiene_limite': False,
        'tiene_multiples_filtros': False,
        'nivel': 'simple'  # simple, medio, complejo
    }
    
    # Verificar componentes
    if extraer_fechas(consulta):
        complejidad['tiene_fechas'] = True
    
    if detectar_agregaciones(consulta):
        complejidad['tiene_agregaciones'] = True
    
    if detectar_ordenamiento(consulta):
        complejidad['tiene_ordenamiento'] = True
    
    if detectar_limite(consulta):
        complejidad['tiene_limite'] = True
    
    # Contar palabras clave de filtros
    palabras_filtro = ['con', 'de', 'mayor', 'menor', 'igual', 'tipo', 'estado', 'entre']
    filtros_encontrados = sum(1 for palabra in palabras_filtro if palabra in consulta_lower)
    
    if filtros_encontrados > 2:
        complejidad['tiene_multiples_filtros'] = True
    
    # Determinar nivel de complejidad
    componentes_activos = sum([
        complejidad['tiene_fechas'],
        complejidad['tiene_agregaciones'],
        complejidad['tiene_ordenamiento'],
        complejidad['tiene_multiples_filtros']
    ])
    
    if componentes_activos == 0:
        complejidad['nivel'] = 'simple'
    elif componentes_activos <= 2:
        complejidad['nivel'] = 'medio'
    else:
        complejidad['nivel'] = 'complejo'
    
    return complejidad


def detectar_formato(consulta):
    """
    Detecta el formato de salida solicitado en la consulta
    
    Args:
        consulta: String con la consulta
    
    Returns:
        String con el formato ('PDF' o 'XLSX'), por defecto 'PDF'
    """
    consulta_lower = consulta.lower()
    
    # Patrones para Excel/XLSX
    patrones_excel = [
        r'en excel',
        r'en xlsx',
        r'formato excel',
        r'formato xlsx',
        r'como excel',
        r'como xlsx',
        r'exportar a excel',
        r'exportar a xlsx',
        r'generar excel',
        r'generar xlsx',
    ]
    
    # Patrones para PDF
    patrones_pdf = [
        r'en pdf',
        r'formato pdf',
        r'como pdf',
        r'exportar a pdf',
        r'generar pdf',
    ]
    
    # Verificar Excel primero (más específico)
    for patron in patrones_excel:
        if re.search(patron, consulta_lower):
            return 'XLSX'
    
    # Verificar PDF
    for patron in patrones_pdf:
        if re.search(patron, consulta_lower):
            return 'PDF'
    
    # Por defecto, retornar PDF
    return 'PDF'


def limpiar_formato_de_consulta(consulta):
    """
    Elimina las referencias al formato de la consulta para procesarla correctamente
    
    Args:
        consulta: String con la consulta original
    
    Returns:
        String con la consulta limpia
    """
    consulta_limpia = consulta
    
    # Patrones a eliminar
    patrones = [
        r'\s+en\s+excel\s*',
        r'\s+en\s+xlsx\s*',
        r'\s+en\s+pdf\s*',
        r'\s+formato\s+excel\s*',
        r'\s+formato\s+xlsx\s*',
        r'\s+formato\s+pdf\s*',
        r'\s+como\s+excel\s*',
        r'\s+como\s+xlsx\s*',
        r'\s+como\s+pdf\s*',
        r'\s+exportar\s+a\s+excel\s*',
        r'\s+exportar\s+a\s+xlsx\s*',
        r'\s+exportar\s+a\s+pdf\s*',
        r'\s+generar\s+excel\s*',
        r'\s+generar\s+xlsx\s*',
        r'\s+generar\s+pdf\s*',
    ]
    
    for patron in patrones:
        consulta_limpia = re.sub(patron, ' ', consulta_limpia, flags=re.IGNORECASE)
    
    # Limpiar espacios múltiples
    consulta_limpia = re.sub(r'\s+', ' ', consulta_limpia).strip()
    
    return consulta_limpia
