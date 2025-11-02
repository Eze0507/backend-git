from rest_framework import serializers
from ..modelsFactProv import FacturaProveedor

class FacturaProveedorSerializer(serializers.ModelSerializer):
    proveedor_nombre = serializers.CharField(source='proveedor.nombre', read_only=True)
    proveedor_nit = serializers.CharField(source='proveedor.nit', read_only=True)
    
    class Meta:
        model = FacturaProveedor
        fields = [
            'id',
            'numero',
            'fecha_registro',
            'observacion',
            'descuento_porcentaje',
            'impuesto_porcentaje',
            'subtotal',
            'descuento',
            'impuesto',
            'total',
            'proveedor',
            'proveedor_nombre',
            'proveedor_nit'
        ]
        # Los montos calculados son read-only, pero los porcentajes son editables
        read_only_fields = ['id', 'descuento', 'impuesto', 'total', 'proveedor_nombre', 'proveedor_nit']
    
    def validate_numero(self, value):
        """Validar que el número de factura sea único"""
        instance = self.instance
        query = FacturaProveedor.objects.filter(numero=value)
        
        # Si estamos editando, excluir la factura actual
        if instance:
            query = query.exclude(pk=instance.pk)
        
        if query.exists():
            raise serializers.ValidationError("Ya existe una factura con este número.")
        return value
    
    def validate_descuento_porcentaje(self, value):
        """Validar que el descuento sea entre 0 y 100"""
        if value < 0 or value > 100:
            raise serializers.ValidationError("El descuento debe estar entre 0 y 100%")
        return value
    
    def validate_impuesto_porcentaje(self, value):
        """Validar que el IVA sea entre 0 y 100"""
        if value < 0 or value > 100:
            raise serializers.ValidationError("El IVA debe estar entre 0 y 100%")
        return value