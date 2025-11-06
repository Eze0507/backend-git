from rest_framework import serializers
from .models import Reporte
from django.contrib.auth.models import User


class UsuarioSimpleSerializer(serializers.ModelSerializer):
    """Serializer simple para mostrar info del usuario"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']


class ReporteSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Reporte"""
    usuario_detalle = UsuarioSimpleSerializer(source='usuario', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    formato_display = serializers.CharField(source='get_formato_display', read_only=True)
    
    class Meta:
        model = Reporte
        fields = [
            'id',
            'usuario',
            'usuario_detalle',
            'tipo',
            'tipo_display',
            'nombre',
            'descripcion',
            'consulta_original',
            'formato',
            'formato_display',
            'archivo',
            'fecha_generacion',
            'registros_procesados',
            'tiempo_generacion',
        ]
        read_only_fields = ['fecha_generacion', 'archivo']


class GenerarReporteEstaticoSerializer(serializers.Serializer):
    """Serializer para generar reportes estáticos"""
    tipo_reporte = serializers.ChoiceField(choices=[
        ('ordenes_estado', 'Órdenes por Estado'),
        ('ordenes_pendientes', 'Órdenes Pendientes'),
        ('ordenes_completadas_mes', 'Órdenes Completadas del Mes'),
        ('ingresos_mensual', 'Ingresos Mensual'),
        ('items_criticos', 'Items con Stock Crítico'),
    ])
    formato = serializers.ChoiceField(choices=['PDF', 'XLSX'], default='PDF')
    fecha_inicio = serializers.DateField(required=False, help_text="Fecha inicio para filtros (opcional)")
    fecha_fin = serializers.DateField(required=False, help_text="Fecha fin para filtros (opcional)")


class ReporteHistorialSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listar historial"""
    usuario_nombre = serializers.CharField(source='usuario.get_full_name', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    formato_display = serializers.CharField(source='get_formato_display', read_only=True)
    
    class Meta:
        model = Reporte
        fields = [
            'id',
            'usuario_nombre',
            'tipo',
            'tipo_display',
            'nombre',
            'formato',
            'formato_display',
            'fecha_generacion',
            'registros_procesados',
        ]


class ReportePersonalizadoSerializer(serializers.Serializer):
    """Serializer para generar reportes personalizados"""
    nombre = serializers.CharField(
        max_length=200,
        help_text="Nombre descriptivo del reporte"
    )
    entidad = serializers.ChoiceField(
        choices=['ordenes', 'clientes', 'vehiculos', 'items'],
        help_text="Entidad sobre la cual generar el reporte"
    )
    campos = serializers.ListField(
        child=serializers.CharField(),
        min_length=1,
        help_text="Lista de campos a incluir en el reporte"
    )
    filtros = serializers.DictField(
        required=False,
        default=dict,
        help_text="Diccionario de filtros a aplicar"
    )
    ordenamiento = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
        help_text="Lista de campos para ordenar (prefijo '-' para descendente)"
    )
    formato = serializers.ChoiceField(
        choices=['PDF', 'XLSX'],
        default='PDF',
        help_text="Formato de salida del reporte"
    )

    def validate(self, data):
        """Validación completa del reporte"""
        from .utils.whitelist import validar_campos, validar_filtros
        
        entidad = data.get('entidad')
        campos = data.get('campos', [])
        filtros = data.get('filtros', {})
        
        # Validar campos
        campos_validos, campos_invalidos = validar_campos(entidad, campos)
        if not campos_validos:
            raise serializers.ValidationError({
                'campos': f"Campos no permitidos: {', '.join(campos_invalidos)}"
            })
        
        # Validar filtros
        filtros_validos, filtros_invalidos = validar_filtros(entidad, filtros)
        if not filtros_validos:
            raise serializers.ValidationError({
                'filtros': f"Filtros no permitidos: {', '.join(filtros_invalidos)}"
            })
        
        return data


class ReporteNaturalSerializer(serializers.Serializer):
    """Serializer para generar reportes usando lenguaje natural"""
    consulta = serializers.CharField(
        max_length=500,
        help_text="Consulta en lenguaje natural (español)"
    )
    nombre = serializers.CharField(
        max_length=200,
        required=False,
        help_text="Nombre del reporte (opcional, se genera automáticamente si no se proporciona)"
    )
    formato = serializers.ChoiceField(
        choices=['PDF', 'XLSX'],
        default='PDF',
        help_text="Formato de salida del reporte"
    )

    def validate_consulta(self, value):
        """Valida que la consulta no esté vacía"""
        if not value or len(value.strip()) < 5:
            raise serializers.ValidationError(
                "La consulta debe tener al menos 5 caracteres"
            )
        return value.strip()
