"""
Utilidades para Backup y Restore del sistema multi-tenant.
Permite exportar e importar todos los datos de un tenant específico.
"""
import json
from datetime import datetime
from decimal import Decimal
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from django.db.models import Q
import logging

from personal_admin.models_saas import Tenant, UserProfile
from personal_admin.models import Cargo, Empleado, Bitacora
from clientes_servicios.models import Cliente, Cita
from operaciones_inventario.modelsVehiculos import Vehiculo, Marca, Modelo
from operaciones_inventario.modelsOrdenTrabajo import (
    OrdenTrabajo, DetalleOrdenTrabajo, NotaOrdenTrabajo, 
    TareaOrdenTrabajo, InventarioVehiculo, Inspeccion, 
    PruebaRuta, AsignacionTecnico, ImagenOrdenTrabajo, DetalleInspeccion
)
from operaciones_inventario.modelsPresupuesto import presupuesto, detallePresupuesto
from operaciones_inventario.modelsItem import Item
from operaciones_inventario.modelsArea import Area
from operaciones_inventario.modelsProveedor import Proveedor
from finanzas_facturacion.models import Pago
from finanzas_facturacion.modelsFactProv import FacturaProveedor
from finanzas_facturacion.modelsDetallesFactProv import DetalleFacturaProveedor
from servicios_IA.models import LecturaPlaca, Reporte

logger = logging.getLogger(__name__)


def export_tenant_data(tenant):
    """
    Exporta todos los datos de un tenant a un diccionario JSON serializable.
    
    Args:
        tenant: Instancia del modelo Tenant
        
    Returns:
        dict: Diccionario con todos los datos del tenant
    """
    try:
        backup_data = {
            'metadata': {
                'version': '1.0',
                'tenant_id': tenant.id,
                'tenant_nombre': tenant.nombre_taller,
                'fecha_backup': datetime.now().isoformat(),
                'django_version': '5.2.6',
            },
            'tenant': {},
            'groups': [],  # Grupos (roles) con sus permisos
            'users': [],
            'user_profiles': [],
            'cargos': [],
            'empleados': [],
            'clientes': [],
            'citas': [],
            'marcas': [],
            'modelos': [],
            'vehiculos': [],
            'areas': [],
            'items': [],
            'proveedores': [],
            'presupuestos': [],
            'detalles_presupuestos': [],
            'ordenes_trabajo': [],
            'detalles_ordenes': [],
            'notas_ordenes': [],
            'tareas_ordenes': [],
            'inventarios_vehiculos': [],
            'inspecciones': [],
            'detalles_inspeccion': [],
            'pruebas_ruta': [],
            'asignaciones_tecnicos': [],
            'imagenes_ordenes': [],
            'pagos': [],
            'facturas_proveedor': [],
            'detalles_facturas_proveedor': [],
            'lecturas_placa': [],
            'reportes': [],
            'bitacoras': [],
        }
        
        # 1. Exportar Tenant
        backup_data['tenant'] = {
            'id': tenant.id,
            'nombre_taller': tenant.nombre_taller,
            'activo': tenant.activo,
            'fecha_creacion': tenant.fecha_creacion.isoformat() if tenant.fecha_creacion else None,
            'propietario_id': tenant.propietario_id,
            'ubicacion': tenant.ubicacion,
            'telefono': tenant.telefono,
            'horarios': tenant.horarios,
            'email_contacto': tenant.email_contacto,
            'logo': tenant.logo,
            'codigo_invitacion': tenant.codigo_invitacion,
        }
        
        # 2. Exportar Grupos (Roles) con sus permisos
        from django.contrib.auth.models import Group, Permission
        # Obtener todos los grupos que están siendo usados por usuarios del tenant
        user_profiles_temp = UserProfile.objects.filter(tenant=tenant).select_related('usuario').prefetch_related('usuario__groups')
        group_ids_used = set()
        for profile in user_profiles_temp:
            group_ids_used.update(profile.usuario.groups.values_list('id', flat=True))
        
        # Exportar TODOS los grupos del sistema (no solo los asignados a usuarios)
        # Esto asegura que roles sin usuarios asignados también se exporten
        for group in Group.objects.all().prefetch_related('permissions'):
            # Exportar permisos con formato "app_label.codename"
            permissions = []
            for perm in group.permissions.all():
                permissions.append(f"{perm.content_type.app_label}.{perm.codename}")
            backup_data['groups'].append({
                'id': group.id,
                'name': group.name,
                'permissions': permissions,
            })
        
        # 3. Exportar UserProfiles y Users relacionados
        user_profiles = UserProfile.objects.filter(tenant=tenant).select_related('usuario').prefetch_related('usuario__groups')
        
        for profile in user_profiles:
            user = profile.usuario
            
            # Obtener nombres de grupos (roles) del usuario
            group_names = list(user.groups.values_list('name', flat=True))
            
            # Datos del usuario
            backup_data['users'].append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'date_joined': user.date_joined.isoformat() if user.date_joined else None,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'groups': group_names,  # Exportar grupos (roles)
            })
            
            # Datos del profile
            backup_data['user_profiles'].append({
                'id': profile.id,
                'usuario_id': profile.usuario_id,
                'tenant_id': profile.tenant_id,
            })
        
        # 4. Exportar Cargos
        for cargo in Cargo.objects.filter(tenant=tenant):
            backup_data['cargos'].append({
                'id': cargo.id,
                'nombre': cargo.nombre,
                'descripcion': cargo.descripcion,
                'sueldo': str(cargo.sueldo),
                'tenant_id': cargo.tenant_id,
            })
        
        # 4. Exportar Empleados
        for empleado in Empleado.objects.filter(tenant=tenant).select_related('cargo', 'usuario', 'area'):
            backup_data['empleados'].append({
                'id': empleado.id,
                'cargo_id': empleado.cargo_id,
                'usuario_id': empleado.usuario_id,
                'area_id': empleado.area_id,
                'tenant_id': empleado.tenant_id,
                'nombre': empleado.nombre,
                'apellido': empleado.apellido,
                'ci': empleado.ci,
                'direccion': empleado.direccion,
                'telefono': empleado.telefono,
                'sexo': empleado.sexo,
                'sueldo': str(empleado.sueldo),
                'estado': empleado.estado,
                'fecha_registro': empleado.fecha_registro.isoformat() if empleado.fecha_registro else None,
                'fecha_actualizado': empleado.fecha_actualizado.isoformat() if empleado.fecha_actualizado else None,
            })
        
        # 5. Exportar Clientes
        for cliente in Cliente.objects.filter(tenant=tenant).select_related('usuario'):
            backup_data['clientes'].append({
                'id': cliente.id,
                'nombre': cliente.nombre,
                'apellido': cliente.apellido,
                'nit': cliente.nit,
                'telefono': cliente.telefono,
                'direccion': cliente.direccion,
                'tipo_cliente': cliente.tipo_cliente,
                'fecha_registro': cliente.fecha_registro.isoformat() if cliente.fecha_registro else None,
                'fecha_actualizacion': cliente.fecha_actualizacion.isoformat() if cliente.fecha_actualizacion else None,
                'activo': cliente.activo,
                'usuario_id': cliente.usuario_id,
                'tenant_id': cliente.tenant_id,
            })
        
        # 6. Exportar Citas
        for cita in Cita.objects.filter(tenant=tenant).select_related('vehiculo', 'empleado', 'cliente'):
            backup_data['citas'].append({
                'id': cita.id,
                'vehiculo_id': cita.vehiculo_id,
                'empleado_id': cita.empleado_id,
                'cliente_id': cita.cliente_id,
                'fecha_hora_inicio': cita.fecha_hora_inicio.isoformat() if cita.fecha_hora_inicio else None,
                'fecha_hora_fin': cita.fecha_hora_fin.isoformat() if cita.fecha_hora_fin else None,
                'estado': cita.estado,
                'tipo_cita': cita.tipo_cita,
                'descripcion': cita.descripcion,
                'nota': cita.nota,
                'fecha_creacion': cita.fecha_creacion.isoformat() if cita.fecha_creacion else None,
                'fecha_actualizacion': cita.fecha_actualizacion.isoformat() if cita.fecha_actualizacion else None,
                'tenant_id': cita.tenant_id,
            })
        
        # 7. Exportar Marcas
        for marca in Marca.objects.filter(tenant=tenant):
            backup_data['marcas'].append({
                'id': marca.id,
                'nombre': marca.nombre,
                'tenant_id': marca.tenant_id,
            })
        
        # 8. Exportar Modelos
        for modelo in Modelo.objects.filter(tenant=tenant).select_related('marca'):
            backup_data['modelos'].append({
                'id': modelo.id,
                'marca_id': modelo.marca_id,
                'nombre': modelo.nombre,
                'tenant_id': modelo.tenant_id,
            })
        
        # 9. Exportar Vehículos
        for vehiculo in Vehiculo.objects.filter(tenant=tenant).select_related('cliente', 'marca', 'modelo'):
            backup_data['vehiculos'].append({
                'id': vehiculo.id,
                'cliente_id': vehiculo.cliente_id,
                'marca_id': vehiculo.marca_id,
                'modelo_id': vehiculo.modelo_id,
                'numero_placa': vehiculo.numero_placa,
                'color': vehiculo.color,
                'año': vehiculo.año,
                'tipo': vehiculo.tipo,
                'vin': vehiculo.vin,
                'numero_motor': vehiculo.numero_motor,
                'version': vehiculo.version,
                'cilindrada': vehiculo.cilindrada,
                'tipo_combustible': vehiculo.tipo_combustible,
                'fecha_registro': vehiculo.fecha_registro.isoformat() if vehiculo.fecha_registro else None,
                'tenant_id': vehiculo.tenant_id,
            })
        
        # 10. Exportar Áreas
        for area in Area.objects.filter(tenant=tenant):
            backup_data['areas'].append({
                'id': area.id,
                'nombre': area.nombre,
                'tenant_id': area.tenant_id,
            })
        
        # 11. Exportar Items
        for item in Item.objects.filter(tenant=tenant):
            backup_data['items'].append({
                'id': item.id,
                'codigo': item.codigo,
                'nombre': item.nombre,
                'descripcion': item.descripcion,
                'precio': str(item.precio) if item.precio else None,
                'costo': str(item.costo) if item.costo else None,
                'stock': item.stock,
                'tipo': item.tipo,
                'fabricante': item.fabricante,
                'imagen': item.imagen,
                'estado': item.estado,
                'area_id': item.area_id,
                'tenant_id': item.tenant_id,
            })
        
        # 12. Exportar Proveedores
        for proveedor in Proveedor.objects.filter(tenant=tenant):
            backup_data['proveedores'].append({
                'id': proveedor.id,
                'nombre': proveedor.nombre,
                'contacto': proveedor.contacto,
                'telefono': proveedor.telefono,
                'correo': proveedor.correo,
                'direccion': proveedor.direccion,
                'nit': proveedor.nit,
                'tenant_id': proveedor.tenant_id,
            })
        
        # 13. Exportar Presupuestos
        for presup in presupuesto.objects.filter(tenant=tenant).select_related('vehiculo', 'cliente'):
            backup_data['presupuestos'].append({
                'id': presup.id,
                'vehiculo_id': presup.vehiculo_id,
                'cliente_id': presup.cliente_id,
                'diagnostico': presup.diagnostico,
                'fecha_inicio': presup.fecha_inicio.isoformat() if presup.fecha_inicio else None,
                'fecha_fin': presup.fecha_fin.isoformat() if presup.fecha_fin else None,
                'estado': presup.estado,
                'con_impuestos': presup.con_impuestos,
                'impuestos': str(presup.impuestos) if presup.impuestos else None,
                'total_descuentos': str(presup.total_descuentos) if presup.total_descuentos else None,
                'subtotal': str(presup.subtotal) if presup.subtotal else None,
                'total': str(presup.total) if presup.total else None,
                'tenant_id': presup.tenant_id,
            })
        
        # 14. Exportar Detalles de Presupuestos
        for detalle in detallePresupuesto.objects.filter(tenant=tenant).select_related('presupuesto', 'item'):
            backup_data['detalles_presupuestos'].append({
                'id': detalle.id,
                'presupuesto_id': detalle.presupuesto_id,
                'item_id': detalle.item_id,
                'cantidad': detalle.cantidad,
                'precio_unitario': str(detalle.precio_unitario) if detalle.precio_unitario else None,
                'descuento_porcentaje': str(detalle.descuento_porcentaje) if detalle.descuento_porcentaje else None,
                'tenant_id': detalle.tenant_id,
            })
        
            # 15. Exportar Órdenes de Trabajo
        for orden in OrdenTrabajo.objects.filter(tenant=tenant).select_related('cliente', 'vehiculo'):
            backup_data['ordenes_trabajo'].append({
                'id': orden.id,
                'cliente_id': orden.cliente_id,
                'vehiculo_id': orden.vehiculo_id,
                'fecha_creacion': orden.fecha_creacion.isoformat() if orden.fecha_creacion else None,
                'fecha_inicio': orden.fecha_inicio.isoformat() if orden.fecha_inicio else None,
                'fecha_finalizacion': orden.fecha_finalizacion.isoformat() if orden.fecha_finalizacion else None,
                'fecha_entrega': orden.fecha_entrega.isoformat() if orden.fecha_entrega else None,
                'estado': orden.estado,
                'kilometraje': str(orden.kilometraje) if orden.kilometraje is not None else '0',
                'nivel_combustible': orden.nivel_combustible,
                'observaciones': orden.observaciones,
                'fallo_requerimiento': orden.fallo_requerimiento,
                'subtotal': str(orden.subtotal) if orden.subtotal is not None else '0.00',
                'impuesto': str(orden.impuesto) if orden.impuesto is not None else '0.00',
                'descuento': str(orden.descuento) if orden.descuento is not None else '0.00',
                'total': str(orden.total) if orden.total is not None else '0.00',
                'tenant_id': orden.tenant_id,
            })        # 16. Exportar Detalles de Órdenes
        for detalle in DetalleOrdenTrabajo.objects.filter(tenant=tenant).select_related('orden_trabajo', 'item'):
            backup_data['detalles_ordenes'].append({
                'id': detalle.id,
                'orden_trabajo_id': detalle.orden_trabajo_id,
                'item_id': detalle.item_id,
                'cantidad': detalle.cantidad,
                'precio_unitario': str(detalle.precio_unitario) if detalle.precio_unitario else None,
                'descuento_porcentaje': str(detalle.descuento_porcentaje) if detalle.descuento_porcentaje else None,
                'tenant_id': detalle.tenant_id,
            })
        
        # 17. Exportar Notas de Órdenes
        for nota in NotaOrdenTrabajo.objects.filter(tenant=tenant).select_related('orden_trabajo'):
            backup_data['notas_ordenes'].append({
                'id': nota.id,
                'orden_trabajo_id': nota.orden_trabajo_id,
                'contenido': nota.contenido,
                'fecha_nota': nota.fecha_nota.isoformat() if nota.fecha_nota else None,
                'tenant_id': nota.tenant_id,
            })
        
        # 18. Exportar Tareas de Órdenes
        for tarea in TareaOrdenTrabajo.objects.filter(tenant=tenant).select_related('orden_trabajo'):
            backup_data['tareas_ordenes'].append({
                'id': tarea.id,
                'orden_trabajo_id': tarea.orden_trabajo_id,
                'descripcion': tarea.descripcion,
                'completada': tarea.completada,
                'tenant_id': tarea.tenant_id,
            })
        
        # 19. Exportar Inventarios de Vehículos
        for inv in InventarioVehiculo.objects.filter(tenant=tenant).select_related('orden_trabajo'):
            backup_data['inventarios_vehiculos'].append({
                'id': inv.id,
                'orden_trabajo_id': inv.orden_trabajo_id,
                'fecha_creacion': inv.fecha_creacion.isoformat() if inv.fecha_creacion else None,
                'extintor': inv.extintor,
                'botiquin': inv.botiquin,
                'antena': inv.antena,
                'llanta_repuesto': inv.llanta_repuesto,
                'documentos': inv.documentos,
                'encendedor': inv.encendedor,
                'pisos': inv.pisos,
                'luces': inv.luces,
                'llaves': inv.llaves,
                'gata': inv.gata,
                'herramientas': inv.herramientas,
                'tapas_ruedas': inv.tapas_ruedas,
                'triangulos': inv.triangulos,
                'tenant_id': inv.tenant_id,
            })
        
        # 20. Exportar Inspecciones
        for inspeccion in Inspeccion.objects.filter(tenant=tenant).select_related('orden_trabajo'):
            backup_data['inspecciones'].append({
                'id': inspeccion.id,
                'orden_trabajo_id': inspeccion.orden_trabajo_id,
                'tipo_inspeccion': inspeccion.tipo_inspeccion,
                'fecha': inspeccion.fecha.isoformat() if inspeccion.fecha else None,
                'tecnico_id': inspeccion.tecnico_id,
                'aceite_motor': inspeccion.aceite_motor,
                'Filtros_VH': inspeccion.Filtros_VH,
                'nivel_refrigerante': inspeccion.nivel_refrigerante,
                'pastillas_freno': inspeccion.pastillas_freno,
                'Estado_neumaticos': inspeccion.Estado_neumaticos,
                'estado_bateria': inspeccion.estado_bateria,
                'estado_luces': inspeccion.estado_luces,
                'observaciones_generales': inspeccion.observaciones_generales,
                'tenant_id': inspeccion.tenant_id,
            })
        
        # 20.1. Exportar Detalles de Inspecciones
        for detalle in DetalleInspeccion.objects.filter(tenant=tenant).select_related('inspeccion'):
            backup_data['detalles_inspeccion'].append({
                'id': detalle.id,
                'inspeccion_id': detalle.inspeccion_id,
                'aceite_motor': detalle.aceite_motor,
                'Filtros_VH': detalle.Filtros_VH,
                'nivel_refrigerante': detalle.nivel_refrigerante,
                'pastillas_freno': detalle.pastillas_freno,
                'Estado_neumaticos': detalle.Estado_neumaticos,
                'estado_bateria': detalle.estado_bateria,
                'estado_luces': detalle.estado_luces,
                'tenant_id': detalle.tenant_id,
            })
        
        # 21. Exportar Pruebas de Ruta
        for prueba in PruebaRuta.objects.filter(tenant=tenant).select_related('orden_trabajo'):
            backup_data['pruebas_ruta'].append({
                'id': prueba.id,
                'orden_trabajo_id': prueba.orden_trabajo_id,
                'tipo_prueba': prueba.tipo_prueba,
                'kilometraje_inicio': prueba.kilometraje_inicio,
                'kilometraje_final': prueba.kilometraje_final,
                'ruta': prueba.ruta,
                'frenos': prueba.frenos,
                'motor': prueba.motor,
                'suspension': prueba.suspension,
                'direccion': prueba.direccion,
                'observaciones': prueba.observaciones,
                'tecnico_id': prueba.tecnico_id,
                'fecha_prueba': prueba.fecha_prueba.isoformat() if prueba.fecha_prueba else None,
                'tenant_id': prueba.tenant_id,
            })
        
        # 22. Exportar Asignaciones de Técnicos
        for asignacion in AsignacionTecnico.objects.filter(tenant=tenant).select_related('orden_trabajo', 'tecnico'):
            backup_data['asignaciones_tecnicos'].append({
                'id': asignacion.id,
                'orden_trabajo_id': asignacion.orden_trabajo_id,
                'tecnico_id': asignacion.tecnico_id,
                'fecha_asignacion': asignacion.fecha_asignacion.isoformat() if asignacion.fecha_asignacion else None,
                'tenant_id': asignacion.tenant_id,
            })
        
        # 23. Exportar Imágenes de Órdenes
        for imagen in ImagenOrdenTrabajo.objects.filter(tenant=tenant).select_related('orden_trabajo'):
            backup_data['imagenes_ordenes'].append({
                'id': imagen.id,
                'orden_trabajo_id': imagen.orden_trabajo_id,
                'imagen_url': imagen.imagen_url,
                'descripcion': imagen.descripcion,
                'tenant_id': imagen.tenant_id,
            })
        
        # 24. Exportar Pagos
        for pago in Pago.objects.filter(tenant=tenant).select_related('orden_trabajo', 'usuario'):
            backup_data['pagos'].append({
                'id': pago.id,
                'orden_trabajo_id': pago.orden_trabajo_id,
                'monto': str(pago.monto),
                'metodo_pago': pago.metodo_pago,
                'estado': pago.estado,
                'fecha_pago': pago.fecha_pago.isoformat() if pago.fecha_pago else None,
                'descripcion': pago.descripcion,
                'stripe_payment_intent_id': pago.stripe_payment_intent_id,
                'numero_referencia': pago.numero_referencia,
                'currency': pago.currency,
                'usuario_id': pago.usuario_id,
                'tenant_id': pago.tenant_id,
            })
        
        # 25. Exportar Facturas de Proveedor
        for factura in FacturaProveedor.objects.filter(tenant=tenant).select_related('proveedor'):
            backup_data['facturas_proveedor'].append({
                'id': factura.id,
                'proveedor_id': factura.proveedor_id,
                'numero': factura.numero,
                'fecha_registro': factura.fecha_registro.isoformat() if factura.fecha_registro else None,
                'observacion': factura.observacion,
                'descuento_porcentaje': str(factura.descuento_porcentaje) if factura.descuento_porcentaje else None,
                'impuesto_porcentaje': str(factura.impuesto_porcentaje) if factura.impuesto_porcentaje else None,
                'subtotal': str(factura.subtotal) if factura.subtotal else None,
                'total': str(factura.total) if factura.total else None,
                'tenant_id': factura.tenant_id,
            })
        
        # 26. Exportar Detalles de Facturas de Proveedor
        for detalle in DetalleFacturaProveedor.objects.filter(tenant=tenant).select_related('factura', 'item'):
            backup_data['detalles_facturas_proveedor'].append({
                'id': detalle.id,
                'factura_id': detalle.factura_id,
                'item_id': detalle.item_id,
                'cantidad': detalle.cantidad,
                'precio_unitario': str(detalle.precio) if detalle.precio else None,
                'descuento_porcentaje': str(detalle.descuento) if detalle.descuento else None,
                'tenant_id': detalle.tenant_id,
            })
        
        # 27. Exportar Lecturas de Placa
        for lectura in LecturaPlaca.objects.filter(tenant=tenant).select_related('vehiculo'):
            backup_data['lecturas_placa'].append({
                'id': lectura.id,
                'placa': lectura.placa,
                'score': str(lectura.score) if lectura.score else None,
                'camera_id': lectura.camera_id,
                'vehiculo_id': lectura.vehiculo_id,
                'match': lectura.match,
                'created_at': lectura.created_at.isoformat() if lectura.created_at else None,
                'tenant_id': lectura.tenant_id,
            })
        
        # 28. Exportar Reportes
        for reporte in Reporte.objects.filter(tenant=tenant):
            backup_data['reportes'].append({
                'id': reporte.id,
                'tipo_reporte': reporte.tipo_reporte,
                'formato': reporte.formato,
                'fecha_generacion': reporte.fecha_generacion.isoformat() if reporte.fecha_generacion else None,
                'archivo': reporte.archivo.url if reporte.archivo else None,
                'tenant_id': reporte.tenant_id,
            })
        
        # 29. Exportar Bitácoras
        for bitacora in Bitacora.objects.filter(tenant=tenant).select_related('usuario'):
            backup_data['bitacoras'].append({
                'id': bitacora.id,
                'usuario_id': bitacora.usuario_id,
                'accion': bitacora.accion,
                'modulo': bitacora.modulo,
                'descripcion': bitacora.descripcion,
                'ip_address': str(bitacora.ip_address) if bitacora.ip_address else None,
                'fecha_accion': bitacora.fecha_accion.isoformat() if bitacora.fecha_accion else None,
                'tenant_id': bitacora.tenant_id,
            })
        
        logger.info(f"Backup exportado exitosamente para tenant: {tenant.nombre_taller}")
        return backup_data
        
    except Exception as e:
        logger.error(f"Error al exportar datos del tenant {tenant.id}: {str(e)}", exc_info=True)
        raise


def import_tenant_data(backup_data, target_tenant, replace=False):
    """
    Importa datos de un backup a un tenant.
    
    Args:
        backup_data: Diccionario con los datos del backup
        target_tenant: Instancia del Tenant destino
        replace: Si True, elimina datos existentes antes de importar
        
    Returns:
        dict: Resumen de la importación
    """
    with transaction.atomic():
        try:
            # Validar versión del backup
            if backup_data.get('metadata', {}).get('version') != '1.0':
                raise ValidationError("Versión de backup no compatible")
            
            summary = {
                'tenant': 0,
                'groups': 0,
                'users': 0,
                'user_profiles': 0,
                'cargos': 0,
                'empleados': 0,
                'clientes': 0,
                'citas': 0,
                'marcas': 0,
                'modelos': 0,
                'vehiculos': 0,
                'areas': 0,
                'items': 0,
                'proveedores': 0,
                'presupuestos': 0,
                'detalles_presupuestos': 0,
                'ordenes_trabajo': 0,
                'detalles_ordenes': 0,
                'notas_ordenes': 0,
                'tareas_ordenes': 0,
                'inventarios_vehiculos': 0,
                'inspecciones': 0,
                'detalles_inspeccion': 0,
                'pruebas_ruta': 0,
                'asignaciones_tecnicos': 0,
                'imagenes_ordenes': 0,
                'pagos': 0,
                'facturas_proveedor': 0,
                'detalles_facturas_proveedor': 0,
                'lecturas_placa': 0,
                'reportes': 0,
                'bitacoras': 0,
                'errors': [],
            }
            
            # Mapeo de IDs antiguos a nuevos
            id_mapping = {
                'users': {},
                'groups': {},
                'cargos': {},
                'areas': {},
                'items': {},
                'marcas': {},
                'modelos': {},
                'clientes': {},
                'vehiculos': {},
                'proveedores': {},
                'empleados': {},
                'presupuestos': {},
                'ordenes_trabajo': {},
                'inspecciones': {},
            }
            
            if replace:
                logger.warning(f"Eliminando datos existentes del tenant {target_tenant.id}")
                # Primero set null foreign keys a empleados del tenant
                empleado_ids = Empleado.objects.filter(tenant=target_tenant).values_list('id', flat=True)
                Inspeccion.objects.filter(Q(tenant=target_tenant) | Q(tecnico__in=empleado_ids)).update(tecnico=None)
                AsignacionTecnico.objects.filter(Q(tenant=target_tenant) | Q(tecnico__in=empleado_ids)).update(tecnico=None)
                PruebaRuta.objects.filter(Q(tenant=target_tenant) | Q(tecnico__in=empleado_ids)).update(tecnico=None)
                Cita.objects.filter(empleado__in=empleado_ids).update(empleado=None)
                # Ahora borrar en orden
                Bitacora.objects.filter(tenant=target_tenant).delete()
                Reporte.objects.filter(tenant=target_tenant).delete()
                LecturaPlaca.objects.filter(tenant=target_tenant).delete()
                Cita.objects.filter(empleado__in=empleado_ids).delete()
                DetalleFacturaProveedor.objects.filter(tenant=target_tenant).delete()
                FacturaProveedor.objects.filter(tenant=target_tenant).delete()
                Pago.objects.filter(tenant=target_tenant).delete()
                ImagenOrdenTrabajo.objects.filter(tenant=target_tenant).delete()
                AsignacionTecnico.objects.filter(tecnico__in=empleado_ids).delete()
                PruebaRuta.objects.filter(tecnico__in=empleado_ids).delete()
                DetalleInspeccion.objects.filter(tenant=target_tenant).delete()
                Inspeccion.objects.filter(tenant=target_tenant).delete()
                InventarioVehiculo.objects.filter(tenant=target_tenant).delete()
                TareaOrdenTrabajo.objects.filter(tenant=target_tenant).delete()
                NotaOrdenTrabajo.objects.filter(tenant=target_tenant).delete()
                DetalleOrdenTrabajo.objects.filter(tenant=target_tenant).delete()
                OrdenTrabajo.objects.filter(tenant=target_tenant).delete()
                detallePresupuesto.objects.filter(tenant=target_tenant).delete()
                presupuesto.objects.filter(tenant=target_tenant).delete()
                Vehiculo.objects.filter(tenant=target_tenant).delete()
                # Intentar eliminar empleados; si falla por FK, limpiar referencias y reintentar
                try:
                    Empleado.objects.filter(tenant=target_tenant).delete()
                except IntegrityError:
                    logger.warning("Fallo al eliminar empleados: limpiando referencias y reintentando")
                    # Asegurar que todos los campos que referencian empleados queden en NULL
                    Inspeccion.objects.filter(tecnico__in=empleado_ids).update(tecnico=None)
                    AsignacionTecnico.objects.filter(tecnico__in=empleado_ids).update(tecnico=None)
                    PruebaRuta.objects.filter(tecnico__in=empleado_ids).update(tecnico=None)
                    Cita.objects.filter(empleado__in=empleado_ids).update(empleado=None)
                    # Reintentar la eliminación
                    Empleado.objects.filter(tenant=target_tenant).delete()
                Cliente.objects.filter(tenant=target_tenant).delete()
                Modelo.objects.filter(tenant=target_tenant).delete()
                Marca.objects.filter(tenant=target_tenant).delete()
                Item.objects.filter(tenant=target_tenant).delete()
                Proveedor.objects.filter(tenant=target_tenant).delete()
                Cargo.objects.filter(tenant=target_tenant).delete()
                Area.objects.filter(tenant=target_tenant).delete()
                # No borrar UserProfile, ya que se recrearán
                # Las eliminaciones se confirmarán automáticamente con la transacción atómica
            
            # Importar (cada operación se ejecutará con autocommit del DB)
            # 0. Importar Grupos (Roles) primero, antes de usuarios
            from django.contrib.auth.models import User, Group, Permission
            for group_data in backup_data.get('groups', []):
                old_id = group_data['id']
                group_name = group_data['name']
                permissions_codenames = group_data.get('permissions', [])
                
                # Crear o obtener el grupo
                group, created = Group.objects.get_or_create(name=group_name)
                
                # Restaurar permisos del grupo
                if permissions_codenames:
                    permissions_to_add = []
                    for codename in permissions_codenames:
                        try:
                            # Buscar permiso por codename (puede tener formato "app.codename" o solo "codename")
                            if '.' in codename:
                                app_label, perm_codename = codename.split('.', 1)
                                permission = Permission.objects.get(codename=perm_codename, content_type__app_label=app_label)
                            else:
                                # Si no tiene app_label, buscar en todos los permisos
                                permission = Permission.objects.filter(codename=codename).first()
                            
                            if permission:
                                permissions_to_add.append(permission)
                        except Permission.DoesNotExist:
                            logger.warning(f"Permiso '{codename}' no encontrado, omitiendo...")
                    
                    # Asignar permisos al grupo
                    if permissions_to_add:
                        group.permissions.set(permissions_to_add)
                        logger.info(f"Permisos restaurados para grupo '{group_name}': {len(permissions_to_add)} permisos")
                
                id_mapping['groups'][old_id] = group.id
                summary['groups'] += 1
            
            # 1. Importar Usuarios (después de grupos)
            for user_data in backup_data.get('users', []):
                old_id = user_data['id']
                user_data.pop('id')
                # Extraer grupos antes de crear el usuario
                group_names = user_data.pop('groups', [])
                # No importar password si no queremos sobreescribir
                password = user_data.pop('password', None)
                user, created = User.objects.get_or_create(
                    username=user_data['username'],
                    defaults=user_data
                )
                if not created and password:
                    # Si ya existe, actualizar campos pero no password por seguridad
                    for key, value in user_data.items():
                        if key not in ['password', 'groups']:
                            setattr(user, key, value)
                    user.save()
                
                # Restaurar grupos (roles) del usuario
                if group_names:
                    groups_to_assign = []
                    for group_name in group_names:
                        try:
                            group = Group.objects.get(name=group_name)
                            groups_to_assign.append(group)
                        except Group.DoesNotExist:
                            # Si el grupo no existe, crear uno básico (aunque debería existir si se importó correctamente)
                            logger.warning(f"Grupo '{group_name}' no existe, creando grupo básico...")
                            try:
                                group = Group.objects.create(name=group_name)
                                groups_to_assign.append(group)
                            except Exception as e:
                                logger.error(f"Error al crear grupo '{group_name}': {e}")
                    
                    # Asignar grupos al usuario
                    if groups_to_assign:
                        user.groups.set(groups_to_assign)
                        logger.info(f"Grupos restaurados para usuario {user.username}: {[g.name for g in groups_to_assign]}")
                
                id_mapping['users'][old_id] = user.id
                summary['users'] += 1
            
            # 1.1. Importar UserProfiles
            for profile_data in backup_data.get('user_profiles', []):
                old_user_id = profile_data.pop('usuario_id')
                profile_data.pop('id')
                profile_data.pop('tenant_id')
                
                if old_user_id in id_mapping['users']:
                    profile_data['usuario_id'] = id_mapping['users'][old_user_id]
                    profile_data['tenant_id'] = target_tenant.id
                    UserProfile.objects.get_or_create(
                        usuario_id=profile_data['usuario_id'],
                        tenant_id=profile_data['tenant_id'],
                        defaults=profile_data
                    )
                    summary['user_profiles'] += 1
            
            # 1. Importar Marcas primero (sin dependencias)
            for marca_data in backup_data.get('marcas', []):
                old_id = marca_data['id']
                marca_data.pop('id')
                marca_data.pop('tenant_id')
                marca, created = Marca.objects.get_or_create(
                    nombre=marca_data['nombre'],
                    tenant=target_tenant,
                    defaults=marca_data
                )
                id_mapping['marcas'][old_id] = marca.id
                summary['marcas'] += 1
            
            # 2. Importar Áreas
            for area_data in backup_data.get('areas', []):
                old_id = area_data['id']
                area_data.pop('id')
                area_data.pop('tenant_id')
                area, created = Area.objects.get_or_create(
                    nombre=area_data['nombre'],
                    tenant=target_tenant,
                    defaults=area_data
                )
                id_mapping['areas'][old_id] = area.id
                summary['areas'] += 1
            
            # 3. Importar Items
            for item_data in backup_data.get('items', []):
                old_id = item_data['id']
                old_area_id = item_data.pop('area_id', None)
                item_data.pop('id')
                item_data.pop('tenant_id')
                
                if old_area_id and old_area_id in id_mapping['areas']:
                    item_data['area_id'] = id_mapping['areas'][old_area_id]
                
                # Convertir campos Decimal de string a Decimal
                for field in ['precio', 'costo']:
                    if field in item_data and item_data[field] is not None:
                        if isinstance(item_data[field], str):
                            item_data[field] = Decimal(item_data[field])
                
                item, created = Item.objects.get_or_create(
                    codigo=item_data['codigo'],
                    tenant=target_tenant,
                    defaults=item_data
                )
                id_mapping['items'][old_id] = item.id
                summary['items'] += 1
            
            # 4. Importar Proveedores
            for proveedor_data in backup_data.get('proveedores', []):
                old_id = proveedor_data['id']
                proveedor_data.pop('id')
                proveedor_data.pop('tenant_id')
                proveedor, created = Proveedor.objects.get_or_create(
                    nombre=proveedor_data['nombre'],
                    tenant=target_tenant,
                    defaults=proveedor_data
                )
                id_mapping['proveedores'][old_id] = proveedor.id
                summary['proveedores'] += 1
            
            # 5. Importar Modelos (después de marcas)
            for modelo_data in backup_data.get('modelos', []):
                old_id = modelo_data['id']
                old_marca_id = modelo_data.pop('marca_id')
                modelo_data.pop('id')
                modelo_data.pop('tenant_id')
                if old_marca_id and old_marca_id in id_mapping['marcas']:
                    modelo_data['marca_id'] = id_mapping['marcas'][old_marca_id]
                    modelo, created = Modelo.objects.get_or_create(
                        nombre=modelo_data['nombre'],
                        marca_id=modelo_data['marca_id'],
                        tenant=target_tenant,
                        defaults=modelo_data
                    )
                    id_mapping['modelos'][old_id] = modelo.id
                    summary['modelos'] += 1
            
            # 6. Importar Cargos
            for cargo_data in backup_data.get('cargos', []):
                old_id = cargo_data['id']
                cargo_data.pop('id')
                cargo_data.pop('tenant_id')
                
                # Convertir campo sueldo de string a Decimal
                if 'sueldo' in cargo_data and cargo_data['sueldo'] is not None:
                    if isinstance(cargo_data['sueldo'], str):
                        cargo_data['sueldo'] = Decimal(cargo_data['sueldo'])
                
                cargo, created = Cargo.objects.get_or_create(
                    nombre=cargo_data['nombre'],
                    tenant=target_tenant,
                    defaults=cargo_data
                )
                id_mapping['cargos'][old_id] = cargo.id
                summary['cargos'] += 1
            
            # 7. Importar Clientes
            for cliente_data in backup_data.get('clientes', []):
                old_id = cliente_data['id']
                old_usuario_id = cliente_data.pop('usuario_id', None)
                cliente_data.pop('id')
                cliente_data.pop('tenant_id')
                
                # Mapear usuario_id si existe
                if old_usuario_id and old_usuario_id in id_mapping['users']:
                    cliente_data['usuario_id'] = id_mapping['users'][old_usuario_id]
                
                cliente, created = Cliente.objects.get_or_create(
                    nit=cliente_data['nit'],
                    tenant=target_tenant,
                    defaults=cliente_data
                )
                id_mapping['clientes'][old_id] = cliente.id
                summary['clientes'] += 1
            
            # 8. Importar Vehículos (después de clientes y modelos)
            for vehiculo_data in backup_data.get('vehiculos', []):
                old_id = vehiculo_data['id']
                old_cliente_id = vehiculo_data.pop('cliente_id')
                old_marca_id = vehiculo_data.pop('marca_id', None)
                old_modelo_id = vehiculo_data.pop('modelo_id', None)
                vehiculo_data.pop('id')
                vehiculo_data.pop('tenant_id')
                
                if old_cliente_id and old_cliente_id in id_mapping['clientes']:
                    vehiculo_data['cliente_id'] = id_mapping['clientes'][old_cliente_id]
                if old_marca_id and old_marca_id in id_mapping['marcas']:
                    vehiculo_data['marca_id'] = id_mapping['marcas'][old_marca_id]
                if old_modelo_id and old_modelo_id in id_mapping['modelos']:
                    vehiculo_data['modelo_id'] = id_mapping['modelos'][old_modelo_id]
                
                vehiculo, created = Vehiculo.objects.get_or_create(
                    numero_placa=vehiculo_data['numero_placa'],
                    tenant=target_tenant,
                    defaults=vehiculo_data
                )
                id_mapping['vehiculos'][old_id] = vehiculo.id
                summary['vehiculos'] += 1
            
            # 9. Importar Empleados (después de cargos y áreas)
            for empleado_data in backup_data.get('empleados', []):
                old_id = empleado_data['id']
                old_cargo_id = empleado_data.pop('cargo_id')
                old_area_id = empleado_data.pop('area_id', None)
                old_usuario_id = empleado_data.pop('usuario_id', None)
                empleado_data.pop('id')
                empleado_data.pop('tenant_id')
                
                if old_cargo_id and old_cargo_id in id_mapping['cargos']:
                    empleado_data['cargo_id'] = id_mapping['cargos'][old_cargo_id]
                if old_area_id and old_area_id in id_mapping['areas']:
                    empleado_data['area_id'] = id_mapping['areas'][old_area_id]
                if old_usuario_id and old_usuario_id in id_mapping['users']:
                    empleado_data['usuario_id'] = id_mapping['users'][old_usuario_id]
                
                # Convertir campo sueldo de string a Decimal
                if 'sueldo' in empleado_data and empleado_data['sueldo'] is not None:
                    if isinstance(empleado_data['sueldo'], str):
                        empleado_data['sueldo'] = Decimal(empleado_data['sueldo'])
                
                empleado, created = Empleado.objects.get_or_create(
                    ci=empleado_data['ci'],
                    tenant=target_tenant,
                    defaults=empleado_data
                )
                id_mapping['empleados'][old_id] = empleado.id
                summary['empleados'] += 1
            
            # 10. Importar Presupuestos (después de vehículos y clientes)
            for presup_data in backup_data.get('presupuestos', []):
                old_id = presup_data['id']
                old_vehiculo_id = presup_data.pop('vehiculo_id', None)
                old_cliente_id = presup_data.pop('cliente_id', None)
                presup_data.pop('id')
                presup_data.pop('tenant_id')
                
                # Mapear FKs
                if old_vehiculo_id and old_vehiculo_id in id_mapping['vehiculos']:
                    presup_data['vehiculo_id'] = id_mapping['vehiculos'][old_vehiculo_id]
                else:
                    presup_data['vehiculo_id'] = None
                    
                if old_cliente_id and old_cliente_id in id_mapping['clientes']:
                    presup_data['cliente_id'] = id_mapping['clientes'][old_cliente_id]
                else:
                    presup_data['cliente_id'] = None
                
                # Asegurar valores por defecto para campos Decimal y eliminar campos None
                if presup_data.get('impuestos') is None or presup_data.get('impuestos') == 'None':
                    presup_data['impuestos'] = '0.00'
                if presup_data.get('total_descuentos') is None or presup_data.get('total_descuentos') == 'None':
                    presup_data['total_descuentos'] = '0.00'
                
                # Convertir campos string a Decimal
                for field in ['impuestos', 'total_descuentos', 'subtotal', 'total']:
                    if field in presup_data and presup_data[field] is not None:
                        if isinstance(presup_data[field], str):
                            presup_data[field] = Decimal(presup_data[field])
                
                # Eliminar campos que sean None para que usen sus defaults del modelo
                if presup_data.get('subtotal') is None or presup_data.get('subtotal') == 'None':
                    presup_data.pop('subtotal', None)
                if presup_data.get('total') is None or presup_data.get('total') == 'None':
                    presup_data.pop('total', None)
                
                try:
                    presup = presupuesto.objects.create(tenant=target_tenant, **presup_data)
                    id_mapping['presupuestos'][old_id] = presup.id
                    summary['presupuestos'] += 1
                except Exception as e:
                    logger.error(f"Error al importar presupuesto {old_id}: {str(e)}")
                    summary['errors'].append(f"Presupuesto {old_id}: {str(e)}")
            
            # 11. Importar Detalles de Presupuestos
            for detalle_data in backup_data.get('detalles_presupuestos', []):
                old_presup_id = detalle_data.pop('presupuesto_id')
                old_item_id = detalle_data.pop('item_id')
                detalle_data.pop('id')
                detalle_data.pop('tenant_id')
                
                if old_presup_id in id_mapping['presupuestos'] and old_item_id in id_mapping['items']:
                    detalle_data['presupuesto_id'] = id_mapping['presupuestos'][old_presup_id]
                    detalle_data['item_id'] = id_mapping['items'][old_item_id]
                    
                    # Asegurar valores por defecto para campos Decimal
                    if detalle_data.get('precio_unitario') is None or detalle_data.get('precio_unitario') == 'None':
                        detalle_data['precio_unitario'] = '0.00'
                    if detalle_data.get('descuento_porcentaje') is None or detalle_data.get('descuento_porcentaje') == 'None':
                        detalle_data['descuento_porcentaje'] = '0.00'
                    if detalle_data.get('cantidad') is None:
                        detalle_data['cantidad'] = 0
                    
                    # Convertir campos string a Decimal
                    for field in ['precio_unitario', 'descuento_porcentaje']:
                        if field in detalle_data and detalle_data[field] is not None:
                            if isinstance(detalle_data[field], str):
                                detalle_data[field] = Decimal(detalle_data[field])
                    
                    # Eliminar campos calculados que pueden ser None
                    detalle_data.pop('subtotal', None)
                    detalle_data.pop('total', None)
                    
                    try:
                        detallePresupuesto.objects.create(tenant=target_tenant, **detalle_data)
                        summary['detalles_presupuestos'] += 1
                    except Exception as e:
                        logger.error(f"Error al importar detalle presupuesto: {str(e)}")
                        summary['errors'].append(f"Detalle presupuesto: {str(e)}")
            
            # 12. Importar Órdenes de Trabajo
            for orden_data in backup_data.get('ordenes_trabajo', []):
                old_id = orden_data['id']
                old_cliente_id = orden_data.pop('cliente_id')
                old_vehiculo_id = orden_data.pop('vehiculo_id')
                orden_data.pop('id')
                orden_data.pop('tenant_id')
                
                if old_cliente_id and old_cliente_id in id_mapping['clientes']:
                    orden_data['cliente_id'] = id_mapping['clientes'][old_cliente_id]
                if old_vehiculo_id and old_vehiculo_id in id_mapping['vehiculos']:
                    orden_data['vehiculo_id'] = id_mapping['vehiculos'][old_vehiculo_id]
                
                # Ensure all decimal and numeric fields have default values (never None)
                if orden_data.get('descuento') is None or orden_data.get('descuento') == 'None':
                    orden_data['descuento'] = '0.00'
                if orden_data.get('impuesto') is None or orden_data.get('impuesto') == 'None':
                    orden_data['impuesto'] = '0.00'
                if orden_data.get('subtotal') is None or orden_data.get('subtotal') == 'None':
                    orden_data['subtotal'] = '0.00'
                if orden_data.get('total') is None or orden_data.get('total') == 'None':
                    orden_data['total'] = '0.00'
                if orden_data.get('kilometraje') is None or orden_data.get('kilometraje') == 'None':
                    orden_data['kilometraje'] = 0
                
                # Convertir campos string a Decimal
                for field in ['descuento', 'impuesto', 'subtotal', 'total']:
                    if field in orden_data and orden_data[field] is not None:
                        if isinstance(orden_data[field], str):
                            orden_data[field] = Decimal(orden_data[field])
                
                orden = OrdenTrabajo.objects.create(tenant=target_tenant, **orden_data)
                id_mapping['ordenes_trabajo'][old_id] = orden.id
                summary['ordenes_trabajo'] += 1
            
            # 13. Importar Detalles de Órdenes
            for detalle_data in backup_data.get('detalles_ordenes', []):
                old_orden_id = detalle_data.pop('orden_trabajo_id')
                old_item_id = detalle_data.pop('item_id', None)
                detalle_data.pop('id')
                detalle_data.pop('tenant_id')
                
                if old_orden_id in id_mapping['ordenes_trabajo']:
                    detalle_data['orden_trabajo_id'] = id_mapping['ordenes_trabajo'][old_orden_id]
                    
                    # Mapear item_id si existe
                    if old_item_id and old_item_id in id_mapping['items']:
                        detalle_data['item_id'] = id_mapping['items'][old_item_id]
                    else:
                        detalle_data['item_id'] = None
                    
                    # Ensure all decimal fields have default values (never None)
                    if detalle_data.get('descuento_porcentaje') is None or detalle_data.get('descuento_porcentaje') == 'None':
                        detalle_data['descuento_porcentaje'] = '0.00'
                    if detalle_data.get('descuento') is None or detalle_data.get('descuento') == 'None':
                        detalle_data['descuento'] = '0.00'
                    if detalle_data.get('subtotal') is None or detalle_data.get('subtotal') == 'None':
                        detalle_data['subtotal'] = '0.00'
                    if detalle_data.get('total') is None or detalle_data.get('total') == 'None':
                        detalle_data['total'] = '0.00'
                    if detalle_data.get('precio_unitario') is None or detalle_data.get('precio_unitario') == 'None':
                        detalle_data['precio_unitario'] = '0.00'
                    if detalle_data.get('cantidad') is None or detalle_data.get('cantidad') == 'None':
                        detalle_data['cantidad'] = 0
                    
                    # Convertir campos string a Decimal
                    for field in ['descuento_porcentaje', 'descuento', 'subtotal', 'total', 'precio_unitario']:
                        if field in detalle_data and detalle_data[field] is not None:
                            if isinstance(detalle_data[field], str):
                                detalle_data[field] = Decimal(detalle_data[field])
                    
                    DetalleOrdenTrabajo.objects.create(tenant=target_tenant, **detalle_data)
                    summary['detalles_ordenes'] += 1
            
            # 14. Importar Notas de Órdenes
            for nota_data in backup_data.get('notas_ordenes', []):
                old_orden_id = nota_data.pop('orden_trabajo_id')
                nota_data.pop('id')
                nota_data.pop('tenant_id')
                
                if old_orden_id in id_mapping['ordenes_trabajo']:
                    nota_data['orden_trabajo_id'] = id_mapping['ordenes_trabajo'][old_orden_id]
                    NotaOrdenTrabajo.objects.create(tenant=target_tenant, **nota_data)
                    summary['notas_ordenes'] += 1
            
            # 15. Importar Tareas de Órdenes
            for tarea_data in backup_data.get('tareas_ordenes', []):
                old_orden_id = tarea_data.pop('orden_trabajo_id')
                tarea_data.pop('id')
                tarea_data.pop('tenant_id')
                
                if old_orden_id in id_mapping['ordenes_trabajo']:
                    tarea_data['orden_trabajo_id'] = id_mapping['ordenes_trabajo'][old_orden_id]
                    TareaOrdenTrabajo.objects.create(tenant=target_tenant, **tarea_data)
                    summary['tareas_ordenes'] += 1
            
            # 16. Importar Inventarios de Vehículos
            for inv_data in backup_data.get('inventarios_vehiculos', []):
                old_orden_id = inv_data.pop('orden_trabajo_id')
                inv_data.pop('id')
                inv_data.pop('tenant_id')
                
                if old_orden_id in id_mapping['ordenes_trabajo']:
                    inv_data['orden_trabajo_id'] = id_mapping['ordenes_trabajo'][old_orden_id]
                    InventarioVehiculo.objects.create(tenant=target_tenant, **inv_data)
                    summary['inventarios_vehiculos'] += 1
            
            # 17. Importar Inspecciones
            for inspeccion_data in backup_data.get('inspecciones', []):
                old_inspeccion_id = inspeccion_data.pop('id')
                old_orden_id = inspeccion_data.pop('orden_trabajo_id')
                inspeccion_data.pop('tenant_id')
                if old_orden_id in id_mapping['ordenes_trabajo']:
                    # Mapear orden
                    inspeccion_data['orden_trabajo_id'] = id_mapping['ordenes_trabajo'][old_orden_id]

                    # Mapear tecnico si existe
                    old_tecnico_id = inspeccion_data.pop('tecnico_id', None)
                    if old_tecnico_id and old_tecnico_id in id_mapping['empleados']:
                        inspeccion_data['tecnico_id'] = id_mapping['empleados'][old_tecnico_id]
                    else:
                        inspeccion_data['tecnico_id'] = None

                    # Crear inspeccion y guardar mapping
                    inspeccion = Inspeccion.objects.create(tenant=target_tenant, **inspeccion_data)
                    id_mapping['inspecciones'][old_inspeccion_id] = inspeccion.id
                    summary['inspecciones'] += 1
            
            # 17.1. Importar Detalles de Inspecciones
            for detalle_data in backup_data.get('detalles_inspeccion', []):
                old_inspeccion_id = detalle_data.pop('inspeccion_id')
                detalle_data.pop('id')
                detalle_data.pop('tenant_id')
                
                if old_inspeccion_id in id_mapping.get('inspecciones', {}):
                    detalle_data['inspeccion_id'] = id_mapping['inspecciones'][old_inspeccion_id]
                    DetalleInspeccion.objects.create(tenant=target_tenant, **detalle_data)
                    summary['detalles_inspeccion'] += 1
            
            # 18. Importar Pruebas de Ruta
            for prueba_data in backup_data.get('pruebas_ruta', []):
                old_orden_id = prueba_data.pop('orden_trabajo_id')
                prueba_data.pop('id')
                prueba_data.pop('tenant_id')
                
                if old_orden_id in id_mapping['ordenes_trabajo']:
                    prueba_data['orden_trabajo_id'] = id_mapping['ordenes_trabajo'][old_orden_id]

                    # Mapear tecnico (si existe en el mapping de empleados)
                    old_tecnico_id = prueba_data.pop('tecnico_id', None)
                    if old_tecnico_id and old_tecnico_id in id_mapping['empleados']:
                        prueba_data['tecnico_id'] = id_mapping['empleados'][old_tecnico_id]
                    else:
                        prueba_data['tecnico_id'] = None

                    # Crear prueba de ruta
                    PruebaRuta.objects.create(tenant=target_tenant, **prueba_data)
                    summary['pruebas_ruta'] += 1
            
            # 19. Importar Asignaciones de Técnicos
            for asignacion_data in backup_data.get('asignaciones_tecnicos', []):
                old_orden_id = asignacion_data.pop('orden_trabajo_id')
                old_tecnico_id = asignacion_data.pop('tecnico_id', asignacion_data.pop('empleado_id', None))
                asignacion_data.pop('id')
                asignacion_data.pop('tenant_id')
                
                if old_orden_id in id_mapping['ordenes_trabajo'] and old_tecnico_id and old_tecnico_id in id_mapping['empleados']:
                    asignacion_data['orden_trabajo_id'] = id_mapping['ordenes_trabajo'][old_orden_id]
                    asignacion_data['tecnico_id'] = id_mapping['empleados'][old_tecnico_id]
                    AsignacionTecnico.objects.create(tenant=target_tenant, **asignacion_data)
                    summary['asignaciones_tecnicos'] += 1
            
            # 20. Importar Imágenes de Órdenes (solo metadatos, no archivos)
            for imagen_data in backup_data.get('imagenes_ordenes', []):
                old_orden_id = imagen_data.pop('orden_trabajo_id')
                imagen_data.pop('id')
                imagen_data.pop('tenant_id')
                imagen_data.pop('imagen', None)
                
                if old_orden_id in id_mapping['ordenes_trabajo']:
                    imagen_data['orden_trabajo_id'] = id_mapping['ordenes_trabajo'][old_orden_id]
                    ImagenOrdenTrabajo.objects.create(tenant=target_tenant, **imagen_data)
                    summary['imagenes_ordenes'] += 1
            
            # 21. Importar Pagos
            for pago_data in backup_data.get('pagos', []):
                old_orden_id = pago_data.pop('orden_trabajo_id')
                pago_data.pop('id')
                pago_data.pop('tenant_id')
                pago_data.pop('usuario_id', None)
                pago_data.pop('stripe_payment_intent_id', None)
                pago_data.pop('stripe_charge_id', None)
                
                if old_orden_id in id_mapping['ordenes_trabajo']:
                    pago_data['orden_trabajo_id'] = id_mapping['ordenes_trabajo'][old_orden_id]
                    
                    # Convertir campo monto de string a Decimal
                    if 'monto' in pago_data and pago_data['monto'] is not None:
                        if isinstance(pago_data['monto'], str):
                            pago_data['monto'] = Decimal(pago_data['monto'])
                    
                    Pago.objects.create(tenant=target_tenant, **pago_data)
                    summary['pagos'] += 1
            
            # 22. Importar Facturas de Proveedor
            for factura_data in backup_data.get('facturas_proveedor', []):
                old_id = factura_data['id']
                old_proveedor_id = factura_data.pop('proveedor_id')
                factura_data.pop('id')
                factura_data.pop('tenant_id')
                
                if old_proveedor_id and old_proveedor_id in id_mapping['proveedores']:
                    factura_data['proveedor_id'] = id_mapping['proveedores'][old_proveedor_id]
                    
                    # Convertir campos Decimal de string a Decimal
                    for field in ['descuento_porcentaje', 'impuesto_porcentaje', 'subtotal', 'descuento', 'impuesto', 'total']:
                        if field in factura_data and factura_data[field] is not None:
                            if isinstance(factura_data[field], str):
                                factura_data[field] = Decimal(factura_data[field])
                    
                    factura = FacturaProveedor.objects.create(tenant=target_tenant, **factura_data)
                    id_mapping['facturas_proveedor'] = id_mapping.get('facturas_proveedor', {})
                    id_mapping['facturas_proveedor'][old_id] = factura.id
                    summary['facturas_proveedor'] += 1
            
            # 23. Importar Detalles de Facturas de Proveedor
            for detalle_data in backup_data.get('detalles_facturas_proveedor', []):
                old_factura_id = detalle_data.pop('factura_id', detalle_data.pop('factura_proveedor_id', None))
                old_item_id = detalle_data.pop('item_id')
                detalle_data.pop('id')
                detalle_data.pop('tenant_id')
                
                facturas_mapping = id_mapping.get('facturas_proveedor', {})
                if old_factura_id in facturas_mapping and old_item_id in id_mapping['items']:
                    detalle_data['factura_id'] = facturas_mapping[old_factura_id]
                    detalle_data['item_id'] = id_mapping['items'][old_item_id]
                    
                    # Mapear nombres de campos del backup a nombres del modelo
                    # El backup usa 'precio_unitario' pero el modelo usa 'precio'
                    if 'precio_unitario' in detalle_data:
                        detalle_data['precio'] = detalle_data.pop('precio_unitario')
                    # El backup usa 'descuento_porcentaje' pero el modelo usa 'descuento'
                    if 'descuento_porcentaje' in detalle_data:
                        detalle_data['descuento'] = detalle_data.pop('descuento_porcentaje')
                    
                    # Convertir campos Decimal de string a Decimal
                    for field in ['precio', 'descuento', 'subtotal', 'total']:
                        if field in detalle_data and detalle_data[field] is not None:
                            if isinstance(detalle_data[field], str):
                                detalle_data[field] = Decimal(detalle_data[field])
                    
                    # Asegurar valores por defecto
                    if detalle_data.get('descuento') is None:
                        detalle_data['descuento'] = Decimal('0.00')
                    if detalle_data.get('cantidad') is None:
                        detalle_data['cantidad'] = 0
                    if detalle_data.get('precio') is None:
                        detalle_data['precio'] = Decimal('0.00')
                    
                    # Calcular subtotal y total si no existen o son None
                    cantidad = detalle_data.get('cantidad', 0)
                    precio = detalle_data.get('precio', Decimal('0.00'))
                    descuento = detalle_data.get('descuento', Decimal('0.00'))
                    
                    # Calcular subtotal = cantidad * precio
                    subtotal = Decimal(str(cantidad)) * precio
                    detalle_data['subtotal'] = subtotal
                    
                    # Calcular total = subtotal - descuento
                    total = subtotal - descuento
                    detalle_data['total'] = total
                    
                    DetalleFacturaProveedor.objects.create(tenant=target_tenant, **detalle_data)
                    summary['detalles_facturas_proveedor'] += 1
            
            # 24. Importar Citas
            for cita_data in backup_data.get('citas', []):
                old_vehiculo_id = cita_data.pop('vehiculo_id', None)
                old_empleado_id = cita_data.pop('empleado_id', None)
                old_cliente_id = cita_data.pop('cliente_id', None)
                cita_data.pop('id')
                cita_data.pop('tenant_id')
                # Remover campos que pueden no existir en versiones antiguas
                cita_data.pop('observaciones', None)
                
                if old_vehiculo_id and old_vehiculo_id in id_mapping['vehiculos']:
                    cita_data['vehiculo_id'] = id_mapping['vehiculos'][old_vehiculo_id]
                if old_empleado_id and old_empleado_id in id_mapping['empleados']:
                    cita_data['empleado_id'] = id_mapping['empleados'][old_empleado_id]
                if old_cliente_id and old_cliente_id in id_mapping['clientes']:
                    cita_data['cliente_id'] = id_mapping['clientes'][old_cliente_id]
                
                Cita.objects.create(tenant=target_tenant, **cita_data)
                summary['citas'] += 1
            
            # 25. Importar Lecturas de Placa
            for lectura_data in backup_data.get('lecturas_placa', []):
                old_vehiculo_id = lectura_data.pop('vehiculo_id', None)
                lectura_data.pop('id')
                lectura_data.pop('tenant_id')
                
                if old_vehiculo_id and old_vehiculo_id in id_mapping['vehiculos']:
                    lectura_data['vehiculo_id'] = id_mapping['vehiculos'][old_vehiculo_id]
                
                LecturaPlaca.objects.create(tenant=target_tenant, **lectura_data)
                summary['lecturas_placa'] += 1
            
            # 26. Importar Reportes (solo metadatos, no archivos)
            for reporte_data in backup_data.get('reportes', []):
                reporte_data.pop('id')
                reporte_data.pop('tenant_id')
                reporte_data.pop('archivo', None)
                Reporte.objects.create(tenant=target_tenant, **reporte_data)
                summary['reportes'] += 1
            
            logger.info(f"Backup importado exitosamente al tenant: {target_tenant.nombre_taller}")
            return summary
        except Exception as e:
            logger.error(f"Error al importar datos al tenant {target_tenant.id}: {str(e)}", exc_info=True)
            raise

