from rest_framework import serializers
from ..modelsServicios import Area, Categoria, Servicio


class AreaSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Area
    """
    
    class Meta:
        model = Area
        fields = ["id", "nombre", "activo", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
    
    def validate_nombre(self, value):
        """
        Validar que el nombre sea único (case-insensitive)
        """
        if self.instance:
            # En caso de actualización, excluir el objeto actual
            if Area.objects.filter(nombre__iexact=value).exclude(pk=self.instance.pk).exists():
                raise serializers.ValidationError("Ya existe un área con este nombre.")
        else:
            # En caso de creación
            if Area.objects.filter(nombre__iexact=value).exists():
                raise serializers.ValidationError("Ya existe un área con este nombre.")
        
        return value.strip()


class CategoriaSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Categoria
    """
    area_detail = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Categoria
        fields = ["id", "nombre", "activo", "area", "area_detail", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
    
    def get_area_detail(self, obj):
        """
        Obtener información detallada del área
        """
        return {
            "id": obj.area.id,
            "nombre": obj.area.nombre
        }
    
    def validate_nombre(self, value):
        """
        Validar que el nombre sea único dentro del área
        """
        area_id = self.initial_data.get('area')
        if not area_id:
            return value
        
        if self.instance:
            # En caso de actualización
            if Categoria.objects.filter(
                area_id=area_id, 
                nombre__iexact=value
            ).exclude(pk=self.instance.pk).exists():
                raise serializers.ValidationError("Ya existe una categoría con este nombre en el área seleccionada.")
        else:
            # En caso de creación
            if Categoria.objects.filter(area_id=area_id, nombre__iexact=value).exists():
                raise serializers.ValidationError("Ya existe una categoría con este nombre en el área seleccionada.")
        
        return value.strip()
    
    def validate(self, data):
        """
        Validación a nivel de serializer
        """
        # No permitir activar categoría si el área está inactiva
        if data.get('activo', True) and 'area' in data:
            area = data['area']
            if not area.activo:
                raise serializers.ValidationError({
                    'activo': 'No se puede activar una categoría si su área está inactiva.'
                })
        
        return data


class ServicioSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Servicio
    """
    categoria_detail = serializers.SerializerMethodField(read_only=True)
    area_detail = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Servicio
        fields = [
            "id", "nombre", "descripcion", "precio", "activo", 
            "categoria", "categoria_detail", "area_detail", 
            "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
    
    def get_categoria_detail(self, obj):
        """
        Obtener información detallada de la categoría
        """
        return {
            "id": obj.categoria.id,
            "nombre": obj.categoria.nombre
        }
    
    def get_area_detail(self, obj):
        """
        Obtener información detallada del área
        """
        return {
            "id": obj.categoria.area.id,
            "nombre": obj.categoria.area.nombre
        }
    
    def validate_precio(self, value):
        """
        Validar que el precio no sea negativo
        """
        if value < 0:
            raise serializers.ValidationError("El precio no puede ser negativo.")
        return value
    
    def validate_nombre(self, value):
        """
        Validar que el nombre sea único dentro de la categoría
        """
        categoria_id = self.initial_data.get('categoria')
        if not categoria_id:
            return value
        
        if self.instance:
            # En caso de actualización
            if Servicio.objects.filter(
                categoria_id=categoria_id, 
                nombre__iexact=value
            ).exclude(pk=self.instance.pk).exists():
                raise serializers.ValidationError("Ya existe un servicio con este nombre en la categoría seleccionada.")
        else:
            # En caso de creación
            if Servicio.objects.filter(categoria_id=categoria_id, nombre__iexact=value).exists():
                raise serializers.ValidationError("Ya existe un servicio con este nombre en la categoría seleccionada.")
        
        return value.strip()
    
    def validate(self, data):
        """
        Validación a nivel de serializer
        """
        # No permitir activar servicio si la categoría está inactiva
        if data.get('activo', True) and 'categoria' in data:
            categoria = data['categoria']
            if not categoria.activo:
                raise serializers.ValidationError({
                    'activo': 'No se puede activar un servicio si su categoría está inactiva.'
                })
            
            # No permitir activar servicio si el área está inactiva
            if not categoria.area.activo:
                raise serializers.ValidationError({
                    'activo': 'No se puede activar un servicio si su área está inactiva.'
                })
        
        return data


# Serializers para listados optimizados (sin detalles adicionales)
class AreaListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listados de áreas
    """
    
    class Meta:
        model = Area
        fields = ["id", "nombre", "activo"]


class CategoriaListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listados de categorías
    """
    area_nombre = serializers.CharField(source='area.nombre', read_only=True)
    
    class Meta:
        model = Categoria
        fields = ["id", "nombre", "activo", "area", "area_nombre"]


class ServicioListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listados de servicios
    """
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    area_nombre = serializers.CharField(source='categoria.area.nombre', read_only=True)
    
    class Meta:
        model = Servicio
        fields = [
            "id", "nombre", "precio", "activo", 
            "categoria", "categoria_nombre", "area_nombre"
        ]
