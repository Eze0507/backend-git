from rest_framework import serializers
from ..modelsDetallesFactProv import DetalleFacturaProveedor


class DetalleFacturaProveedorSerializer(serializers.ModelSerializer):
    item_nombre = serializers.CharField(source='item.nombre', read_only=True)
    item_codigo = serializers.CharField(source='item.codigo', read_only=True)
    factura_numero = serializers.CharField(source='factura.numero', read_only=True)
    
    class Meta:
        model = DetalleFacturaProveedor
        fields = [
            'id',
            'factura',
            'factura_numero',
            'item',
            'item_nombre',
            'item_codigo',
            'cantidad',
            'precio',
            'descuento',
            'subtotal',
            'total'
        ]
        read_only_fields = ['id']
    
    def validate_cantidad(self, value):
        """Validar que la cantidad sea mayor a 0"""
        if value <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor a 0.")
        return value
    
    def validate_precio(self, value):
        """Validar que el precio sea mayor o igual a 0"""
        if value < 0:
            raise serializers.ValidationError("El precio no puede ser negativo.")
        return value
    
    def validate(self, data):
        """Validar que el subtotal y total sean correctos"""
        cantidad = data.get('cantidad', 0)
        precio = data.get('precio', 0)
        descuento = data.get('descuento', 0)
        subtotal = data.get('subtotal', 0)
        total = data.get('total', 0)
        
        # Calcular subtotal esperado
        subtotal_calculado = cantidad * precio
        
        if abs(subtotal - subtotal_calculado) > 0.01:
            raise serializers.ValidationError(
                f"El subtotal no coincide. Calculado: {subtotal_calculado}, Recibido: {subtotal}"
            )
        
        # Calcular total esperado
        total_calculado = subtotal - descuento
        
        if abs(total - total_calculado) > 0.01:
            raise serializers.ValidationError(
                f"El total no coincide. Calculado: {total_calculado}, Recibido: {total}"
            )
        
        return data
