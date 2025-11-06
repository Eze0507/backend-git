"""
Vistas para el módulo de Reportes
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import FileResponse
from django.utils import timezone
from django.db.models import Sum, Count, Q, F
from django.apps import apps
from datetime import datetime, timedelta
import time
import json

from .models import Reporte
from personal_admin.views import registrar_bitacora
from personal_admin.models import Bitacora
from .serializersReporte import (
    ReporteSerializer,
    GenerarReporteEstaticoSerializer,
    ReporteHistorialSerializer,
    ReporteNaturalSerializer
)
from .utils.reportes_config import obtener_config_reporte, listar_reportes_disponibles
from .utils.pdf_generator import generar_pdf_simple
from .utils.excel_generator import generar_excel
from .utils.nl_parser import interpretar_consulta, generar_ejemplos_consultas


class ReporteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar reportes
    """
    serializer_class = ReporteSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Cada usuario solo ve sus propios reportes
        return Reporte.objects.filter(usuario=self.request.user)
    
    @action(detail=False, methods=['get'])
    def disponibles(self, request):
        """
        Lista los reportes estáticos disponibles
        GET /api/ia/reportes/disponibles/
        """
        reportes = listar_reportes_disponibles()
        return Response({
            'success': True,
            'reportes': reportes
        })
    
    @action(detail=False, methods=['get'])
    def entidades(self, request):
        """
        Lista las entidades disponibles para reportes personalizados
        GET /api/ia/reportes/entidades/
        """
        from .utils.whitelist import obtener_entidades
        entidades = obtener_entidades()
        return Response({
            'success': True,
            'entidades': list(entidades.values())
        })
    
    @action(detail=False, methods=['get'], url_path='entidades/(?P<entidad_id>[^/.]+)/campos')
    def campos_entidad(self, request, entidad_id=None):
        """
        Obtiene los campos y filtros disponibles para una entidad
        GET /api/ia/reportes/entidades/{entidad_id}/campos/
        """
        from .utils.whitelist import obtener_config_entidad
        
        config = obtener_config_entidad(entidad_id)
        if not config:
            return Response({
                'success': False,
                'error': 'Entidad no encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': True,
            'entidad': config['nombre'],
            'campos': [
                {
                    'id': key,
                    'label': value['label'],
                    'tipo': value['tipo']
                }
                for key, value in config['campos_disponibles'].items()
            ],
            'filtros': [
                {
                    'id': key,
                    **value
                }
                for key, value in config['filtros_disponibles'].items()
            ]
        })
    
    @action(detail=False, methods=['post'])
    def generar_estatico(self, request):
        """
        Genera un reporte estático predefinido
        POST /api/ia/reportes/generar_estatico/
        {
            "tipo_reporte": "ordenes_estado",
            "formato": "PDF",
            "fecha_inicio": "2025-01-01",  // opcional
            "fecha_fin": "2025-01-31"      // opcional
        }
        """
        serializer = GenerarReporteEstaticoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        tipo_reporte = serializer.validated_data['tipo_reporte']
        formato = serializer.validated_data['formato']
        fecha_inicio = serializer.validated_data.get('fecha_inicio')
        fecha_fin = serializer.validated_data.get('fecha_fin')
        
        # Obtener configuración del reporte
        config = obtener_config_reporte(tipo_reporte)
        if not config:
            return Response({
                'success': False,
                'error': 'Tipo de reporte no válido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            tiempo_inicio = time.time()
            
            # Generar los datos del reporte
            datos = self._generar_datos_reporte(config, fecha_inicio, fecha_fin)
            
            # Generar el archivo según formato
            if formato == 'PDF':
                archivo = self._generar_pdf_reporte(config, datos)
                nombre_archivo = f"{tipo_reporte}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            else:  # XLSX
                archivo = self._generar_excel_reporte(config, datos)
                nombre_archivo = f"{tipo_reporte}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            tiempo_fin = time.time()
            tiempo_generacion = tiempo_fin - tiempo_inicio
            
            # Guardar registro en base de datos
            reporte = Reporte.objects.create(
                usuario=request.user,
                tipo='ESTATICO',
                nombre=config['nombre'],
                descripcion=config['descripcion'],
                consulta_original=json.dumps({
                    'tipo_reporte': tipo_reporte,
                    'fecha_inicio': str(fecha_inicio) if fecha_inicio else None,
                    'fecha_fin': str(fecha_fin) if fecha_fin else None
                }),
                formato=formato,
                registros_procesados=len(datos['registros']),
                tiempo_generacion=round(tiempo_generacion, 2)
            )
            
            # Guardar el archivo
            reporte.archivo.save(nombre_archivo, archivo, save=True)
            
            # Registrar en bitácora
            descripcion = f"Reporte estático '{config['nombre']}' generado en formato {formato}. Registros procesados: {len(datos['registros'])}, Tiempo: {round(tiempo_generacion, 2)}s"
            registrar_bitacora(
                usuario=request.user,
                accion=Bitacora.Accion.CREAR,
                modulo=Bitacora.Modulo.REPORTE,
                descripcion=descripcion,
                request=request
            )
            
            return Response({
                'success': True,
                'message': 'Reporte generado exitosamente',
                'reporte': ReporteSerializer(reporte).data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error al generar reporte: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def descargar(self, request, pk=None):
        """
        Descarga un reporte generado
        GET /api/ia/reportes/{id}/descargar/
        """
        reporte = self.get_object()
        
        if not reporte.archivo:
            return Response({
                'success': False,
                'error': 'Este reporte no tiene archivo asociado'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Registrar en bitácora la descarga
        descripcion = f"Descarga de reporte '{reporte.nombre}' (ID: {reporte.id}, Tipo: {reporte.tipo}, Formato: {reporte.formato})"
        registrar_bitacora(
            usuario=request.user,
            accion=Bitacora.Accion.CONSULTAR,
            modulo=Bitacora.Modulo.REPORTE,
            descripcion=descripcion,
            request=request
        )
        
        # Devolver el archivo
        response = FileResponse(
            reporte.archivo.open('rb'),
            content_type='application/pdf' if reporte.formato == 'PDF' else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{reporte.archivo.name.split("/")[-1]}"'
        
        return response
    
    @action(detail=False, methods=['get'])
    def historial(self, request):
        """
        Obtiene el historial de reportes del usuario
        GET /api/ia/reportes/historial/
        """
        reportes = self.get_queryset()[:20]  # Últimos 20
        serializer = ReporteHistorialSerializer(reportes, many=True)
        
        return Response({
            'success': True,
            'reportes': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def entidades(self, request):
        """
        Obtiene la lista de entidades disponibles con sus campos y filtros
        GET /api/ia/reportes/entidades/
        """
        from .utils.whitelist import ENTIDADES_DISPONIBLES
        
        return Response({
            'success': True,
            'entidades': ENTIDADES_DISPONIBLES
        })
    
    @action(detail=False, methods=['post'], url_path='generar-personalizado')
    def generar_personalizado(self, request):
        """
        Genera un reporte personalizado según campos y filtros seleccionados
        POST /api/ia/reportes/generar-personalizado/
        {
            "nombre": "Mi Reporte",
            "entidad": "ordenes",
            "campos": ["id", "fecha_creacion", "cliente__nombre", "total"],
            "filtros": {"estado": "pendiente"},
            "ordenamiento": ["-fecha_creacion"],
            "formato": "PDF"
        }
        """
        from .serializersReporte import ReportePersonalizadoSerializer
        from .utils.whitelist import obtener_config_entidad
        from django.core.serializers.json import DjangoJSONEncoder
        
        serializer = ReportePersonalizadoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        try:
            tiempo_inicio = time.time()
            
            # Obtener configuración de la entidad
            config_entidad = obtener_config_entidad(data['entidad'])
            if not config_entidad:
                return Response({
                    'success': False,
                    'error': 'Entidad no encontrada'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Obtener el modelo
            app_label, model_name = config_entidad['modelo'].split('.')
            Model = apps.get_model(app_label, model_name)
            
            # Construir queryset
            queryset = Model.objects.all()
            
            # Aplicar select_related según el modelo para optimizar queries
            if model_name == 'OrdenTrabajo':
                queryset = queryset.select_related('cliente', 'vehiculo', 'vehiculo__marca', 'vehiculo__modelo', 'tecnico')
            elif model_name == 'Item':
                queryset = queryset.select_related('area')
            elif model_name == 'Vehiculo':
                queryset = queryset.select_related('cliente', 'marca', 'modelo')
            
            # Aplicar filtros si existen
            if data.get('filtros'):
                queryset = queryset.filter(**data['filtros'])
            
            # Aplicar ordenamiento
            if data.get('ordenamiento'):
                queryset = queryset.order_by(*data['ordenamiento'])
            
            # Obtener datos
            registros = []
            for obj in queryset:
                registro = {}
                for campo in data['campos']:
                    valor = self._obtener_valor_campo(obj, campo)
                    registro[campo] = valor
                registros.append(registro)
            
            # Preparar datos para generación
            datos_reporte = {
                'nombre': data['nombre'],
                'entidad': config_entidad['nombre'],
                'campos': data['campos'],
                'registros': registros,
                'total_registros': len(registros)
            }
            
            # Generar archivo según formato
            if data['formato'] == 'PDF':
                archivo = self._generar_pdf_personalizado(datos_reporte, config_entidad)
                nombre_archivo = f"{data['entidad']}_personalizado_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            else:  # XLSX
                archivo = self._generar_excel_personalizado(datos_reporte, config_entidad)
                nombre_archivo = f"{data['entidad']}_personalizado_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            tiempo_fin = time.time()
            tiempo_generacion = tiempo_fin - tiempo_inicio
            
            # Guardar registro en base de datos
            reporte = Reporte.objects.create(
                usuario=request.user,
                tipo='PERSONALIZADO',
                nombre=data['nombre'],
                descripcion=f"Reporte personalizado de {config_entidad['nombre']}",
                consulta_original=json.dumps(data, cls=DjangoJSONEncoder),
                formato=data['formato'],
                registros_procesados=len(registros),
                tiempo_generacion=round(tiempo_generacion, 2)
            )
            
            # Guardar el archivo
            reporte.archivo.save(nombre_archivo, archivo, save=True)
            
            # Registrar en bitácora
            descripcion = f"Reporte personalizado '{data['nombre']}' generado para entidad {config_entidad['nombre']} en formato {data['formato']}. Campos: {len(data['campos'])}, Filtros: {len(data.get('filtros', {}))}, Registros: {len(registros)}, Tiempo: {round(tiempo_generacion, 2)}s"
            registrar_bitacora(
                usuario=request.user,
                accion=Bitacora.Accion.CREAR,
                modulo=Bitacora.Modulo.REPORTE,
                descripcion=descripcion,
                request=request
            )
            
            from .serializersReporte import ReporteSerializer
            return Response({
                'success': True,
                'message': 'Reporte personalizado generado exitosamente',
                'reporte': ReporteSerializer(reporte).data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error al generar reporte: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='generar-natural')
    def generar_natural(self, request):
        """
        Genera un reporte usando lenguaje natural
        POST /api/ia/reportes/generar-natural/
        Body: {
            "consulta": "Órdenes completadas este mes",
            "nombre": "Mi reporte" (opcional),
            "formato": "PDF" o "XLSX"
        }
        """
        from django.core.serializers.json import DjangoJSONEncoder
        from .utils.whitelist import obtener_config_entidad
        
        serializer = ReporteNaturalSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        consulta = data['consulta']
        
        try:
            tiempo_inicio = time.time()
            
            # Interpretar la consulta en lenguaje natural
            interpretacion = interpretar_consulta(consulta)
            
            # Verificar si hubo error en la interpretación
            if interpretacion.get('error'):
                return Response({
                    'success': False,
                    'error': interpretacion['error'],
                    'sugerencias': generar_ejemplos_consultas()
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Obtener configuración de la entidad
            entidad = interpretacion['entidad']
            config_entidad = obtener_config_entidad(entidad)
            if not config_entidad:
                return Response({
                    'success': False,
                    'error': 'Entidad no encontrada'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Usar campos sugeridos o todos los campos disponibles
            campos = interpretacion.get('campos_sugeridos', list(config_entidad['campos_disponibles'].keys())[:8])
            filtros = interpretacion.get('filtros', {})
            
            # Obtener el modelo
            app_label, model_name = config_entidad['modelo'].split('.')
            Model = apps.get_model(app_label, model_name)
            
            # Construir queryset
            queryset = Model.objects.all()
            
            # Aplicar select_related según el modelo para optimizar queries
            if model_name == 'OrdenTrabajo':
                queryset = queryset.select_related('cliente', 'vehiculo', 'vehiculo__marca', 'vehiculo__modelo')
            elif model_name == 'Item':
                queryset = queryset.select_related('area')
            elif model_name == 'Vehiculo':
                queryset = queryset.select_related('cliente', 'marca', 'modelo')
            elif model_name == 'Cliente':
                pass  # Cliente no tiene relaciones que optimizar en este contexto
            
            # Aplicar filtros
            if filtros:
                queryset = queryset.filter(**filtros)
            
            # Obtener datos
            registros = []
            for obj in queryset:
                registro = {}
                for campo in campos:
                    valor = self._obtener_valor_campo(obj, campo)
                    registro[campo] = valor
                registros.append(registro)
            
            # Generar nombre automático si no se proporcionó
            nombre = data.get('nombre') or f"Reporte: {consulta[:50]}"
            
            # Preparar datos para generación
            datos_reporte = {
                'nombre': nombre,
                'entidad': config_entidad['nombre'],
                'campos': campos,
                'registros': registros,
                'total_registros': len(registros),
                'consulta_interpretada': interpretacion
            }
            
            # Generar archivo según formato
            if data['formato'] == 'PDF':
                archivo = self._generar_pdf_personalizado(datos_reporte, config_entidad)
                nombre_archivo = f"{entidad}_natural_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            else:  # XLSX
                archivo = self._generar_excel_personalizado(datos_reporte, config_entidad)
                nombre_archivo = f"{entidad}_natural_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            tiempo_fin = time.time()
            tiempo_generacion = tiempo_fin - tiempo_inicio
            
            # Guardar registro en base de datos
            reporte = Reporte.objects.create(
                usuario=request.user,
                tipo='NATURAL',
                nombre=nombre,
                descripcion=f"Consulta: {consulta}",
                consulta_original=json.dumps({
                    'consulta': consulta,
                    'interpretacion': interpretacion,
                    'campos': campos,
                    'filtros': filtros
                }, cls=DjangoJSONEncoder),
                formato=data['formato'],
                registros_procesados=len(registros),
                tiempo_generacion=round(tiempo_generacion, 2)
            )
            
            # Guardar el archivo
            reporte.archivo.save(nombre_archivo, archivo, save=True)
            
            # Registrar en bitácora
            descripcion = f"Reporte con lenguaje natural '{nombre}' generado. Consulta: '{consulta}'. Entidad: {config_entidad['nombre']}, Formato: {data['formato']}, Registros: {len(registros)}, Tiempo: {round(tiempo_generacion, 2)}s"
            registrar_bitacora(
                usuario=request.user,
                accion=Bitacora.Accion.CREAR,
                modulo=Bitacora.Modulo.REPORTE,
                descripcion=descripcion,
                request=request
            )
            
            return Response({
                'success': True,
                'message': 'Reporte generado exitosamente desde lenguaje natural',
                'reporte': ReporteSerializer(reporte).data,
                'interpretacion': {
                    'entidad': config_entidad['nombre'],
                    'filtros_aplicados': filtros,
                    'campos_incluidos': campos,
                    'registros_encontrados': len(registros)
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            import traceback
            return Response({
                'success': False,
                'error': f'Error al generar reporte: {str(e)}',
                'traceback': traceback.format_exc()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def ejemplos_nl(self, request):
        """
        Retorna ejemplos de consultas en lenguaje natural
        GET /api/ia/reportes/ejemplos-nl/
        """
        ejemplos = generar_ejemplos_consultas()
        return Response({
            'success': True,
            'ejemplos': ejemplos
        })
    
    def _generar_datos_reporte(self, config, fecha_inicio=None, fecha_fin=None):
        """
        Genera los datos para el reporte según la configuración
        """
        # Obtener el modelo dinámicamente
        app_label, model_name = config['modelo'].split('.')
        Model = apps.get_model(app_label, model_name)
        
        # Construir filtros
        filtros = self._construir_filtros(config['filtros_default'], fecha_inicio, fecha_fin)
        
        # Construir queryset base
        queryset = Model.objects.filter(**filtros) if filtros else Model.objects.all()
        
        # Aplicar select_related solo si el modelo es OrdenTrabajo
        if model_name == 'OrdenTrabajo':
            queryset = queryset.select_related('cliente', 'vehiculo', 'vehiculo__marca', 'vehiculo__modelo')
            # Manejo especial para órdenes pendientes (sin filtros en config)
            if not filtros:
                queryset = queryset.filter(estado__in=['pendiente', 'en_proceso'])
        elif model_name == 'Item':
            queryset = queryset.select_related('area')
        
        # Extraer valores
        registros = []
        for obj in queryset:
            registro = {}
            for campo in config['campos']:
                valor = self._obtener_valor_campo(obj, campo)
                registro[campo] = valor
            registros.append(registro)
        
        return {
            'nombre': config['nombre'],
            'descripcion': config['descripcion'],
            'campos': config['campos'],
            'registros': registros,
            'total_registros': len(registros)
        }
    
    def _construir_filtros(self, filtros_default, fecha_inicio, fecha_fin):
        """
        Construye el diccionario de filtros reemplazando valores especiales
        """
        filtros = {}
        
        for key, value in filtros_default.items():
            if value == 'hace_30_dias':
                filtros[key] = timezone.now() - timedelta(days=30)
            elif value == 'mes_actual':
                filtros[key] = timezone.now().month
            elif value == 'anio_actual':
                filtros[key] = timezone.now().year
            elif value == 'stock_minimo':
                # Filtro especial para items críticos
                continue  # Se maneja con F()
            else:
                # Manejar listas y otros valores directamente
                filtros[key] = value
        
        # Filtros personalizados de fechas
        if fecha_inicio:
            filtros['fecha_creacion__gte'] = fecha_inicio
        if fecha_fin:
            filtros['fecha_creacion__lte'] = fecha_fin
        
        return filtros
    
    def _obtener_valor_campo(self, obj, campo):
        """
        Obtiene el valor de un campo, incluso si es relación (con __)
        """
        try:
            if '__' in campo:
                # Campo con relación
                partes = campo.split('__')
                valor = obj
                for parte in partes:
                    valor = getattr(valor, parte, '')
                    if valor is None:
                        return ''
                return valor
            else:
                return getattr(obj, campo, '')
        except:
            return ''
    
    def _generar_pdf_reporte(self, config, datos):
        """
        Genera el PDF del reporte usando ReportLab
        """
        # Preparar encabezados
        encabezados = [
            campo.replace('__', ' ').replace('_', ' ').title()
            for campo in datos['campos']
        ]
        
        # Preparar datos
        filas = []
        for registro in datos['registros']:
            fila = [str(registro.get(campo, '')) for campo in datos['campos']]
            filas.append(fila)
        
        # Preparar información adicional
        info_adicional = {
            'Total de registros': datos['total_registros']
        }
        
        # Generar PDF
        datos_pdf = {
            'titulo': datos['nombre'],
            'subtitulo': datos['descripcion'],
            'encabezados': encabezados,
            'datos': filas,
            'info_adicional': info_adicional
        }
        
        return generar_pdf_simple(datos_pdf)
    
    def _generar_excel_reporte(self, config, datos):
        """
        Genera el Excel del reporte
        """
        # Preparar encabezados
        encabezados = [
            campo.replace('__', ' ').replace('_', ' ').title()
            for campo in datos['campos']
        ]
        
        # Preparar datos
        filas = []
        for registro in datos['registros']:
            fila = [registro.get(campo, '') for campo in datos['campos']]
            filas.append(fila)
        
        return generar_excel(
            titulo=datos['nombre'],
            encabezados=encabezados,
            datos=filas,
            hoja_nombre="Reporte"
        )
    
    def _generar_pdf_personalizado(self, datos_reporte, config_entidad):
        """
        Genera el PDF para un reporte personalizado
        """
        # Preparar encabezados con etiquetas amigables
        encabezados = []
        for campo in datos_reporte['campos']:
            if campo in config_entidad['campos_disponibles']:
                encabezados.append(config_entidad['campos_disponibles'][campo]['label'])
            else:
                encabezados.append(campo.replace('__', ' ').replace('_', ' ').title())
        
        # Preparar datos
        filas = []
        for registro in datos_reporte['registros']:
            fila = [str(registro.get(campo, '')) for campo in datos_reporte['campos']]
            filas.append(fila)
        
        # Preparar información adicional
        info_adicional = {
            'Entidad': datos_reporte['entidad'],
            'Total de registros': datos_reporte['total_registros']
        }
        
        # Generar PDF
        datos_pdf = {
            'titulo': datos_reporte['nombre'],
            'subtitulo': f"Reporte personalizado de {datos_reporte['entidad']}",
            'encabezados': encabezados,
            'datos': filas,
            'info_adicional': info_adicional
        }
        
        return generar_pdf_simple(datos_pdf)
    
    def _generar_excel_personalizado(self, datos_reporte, config_entidad):
        """
        Genera el Excel para un reporte personalizado
        """
        # Preparar encabezados con etiquetas amigables
        encabezados = []
        for campo in datos_reporte['campos']:
            if campo in config_entidad['campos_disponibles']:
                encabezados.append(config_entidad['campos_disponibles'][campo]['label'])
            else:
                encabezados.append(campo.replace('__', ' ').replace('_', ' ').title())
        
        # Preparar datos
        filas = []
        for registro in datos_reporte['registros']:
            fila = [registro.get(campo, '') for campo in datos_reporte['campos']]
            filas.append(fila)
        
        return generar_excel(
            titulo=datos_reporte['nombre'],
            encabezados=encabezados,
            datos=filas,
            hoja_nombre="Reporte Personalizado"
        )
