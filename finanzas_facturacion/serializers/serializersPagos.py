from rest_framework import serializers
from ..models import Pago
from operaciones_inventario.modelsOrdenTrabajo import OrdenTrabajo


class PagoSerializer(serializers.ModelSerializer):
    """Serializer principal para el modelo Pago"""
    
    orden_trabajo_id = serializers.IntegerField(source='orden_trabajo.id', read_only=True)
    orden_trabajo_numero = serializers.CharField(source='orden_trabajo.numero_orden', read_only=True)
    cliente_nombre = serializers.SerializerMethodField()
    usuario_nombre = serializers.SerializerMethodField()
    metodo_pago_display = serializers.CharField(source='get_metodo_pago_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    
    class Meta:
        model = Pago
        fields = [
            'id', 
            'orden_trabajo',
            'orden_trabajo_id',
            'orden_trabajo_numero',
            'cliente_nombre',
            'monto', 
            'metodo_pago',
            'metodo_pago_display',
            'estado',
            'estado_display',
            'fecha_pago',
            'fecha_actualizacion',
            'stripe_payment_intent_id',
            'currency',
            'descripcion',
            'numero_referencia',
            'usuario',
            'usuario_nombre',
        ]
        read_only_fields = [
            'fecha_pago', 
            'fecha_actualizacion',
            'stripe_payment_intent_id'
        ]
    
    def get_cliente_nombre(self, obj):
        """Obtener el nombre completo del cliente de la orden"""
        if obj.orden_trabajo and obj.orden_trabajo.cliente:
            return f"{obj.orden_trabajo.cliente.nombre} {obj.orden_trabajo.cliente.apellido}"
        return None
    
    def get_usuario_nombre(self, obj):
        """Obtener el nombre del usuario que registró el pago"""
        if obj.usuario:
            return f"{obj.usuario.first_name} {obj.usuario.last_name}".strip() or obj.usuario.username
        return None


class PagoCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear pagos manuales (efectivo, transferencia, etc.)"""
    
    class Meta:
        model = Pago
        fields = [
            'orden_trabajo',
            'monto',
            'metodo_pago',
            'descripcion',
            'numero_referencia',
        ]
    
    def validate_orden_trabajo(self, value):
        """Validar que la orden de trabajo existe y está en estado válido"""
        if not OrdenTrabajo.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("La orden de trabajo no existe")
        return value
    
    def validate_monto(self, value):
        """Validar que el monto sea positivo"""
        if value <= 0:
            raise serializers.ValidationError("El monto debe ser mayor a 0")
        return value


class StripePaymentIntentSerializer(serializers.Serializer):
    """Serializer para crear un Payment Intent de Stripe"""
    
    orden_trabajo_id = serializers.IntegerField()
    monto = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=False,
        help_text="Si no se proporciona, se usará el total de la orden"
    )
    descripcion = serializers.CharField(
        required=False,
        max_length=500,
        help_text="Descripción opcional del pago"
    )
    
    def validate_orden_trabajo_id(self, value):
        """Validar que la orden existe"""
        if not OrdenTrabajo.objects.filter(id=value).exists():
            raise serializers.ValidationError("La orden de trabajo no existe")
        return value
    
    def validate_monto(self, value):
        """Validar que el monto sea positivo"""
        if value and value <= 0:
            raise serializers.ValidationError("El monto debe ser mayor a 0")
        return value


class StripeConfirmPaymentSerializer(serializers.Serializer):
    """Serializer para confirmar un pago de Stripe"""
    
    payment_intent_id = serializers.CharField(
        max_length=255,
        help_text="ID del Payment Intent de Stripe"
    )
    
    def validate_payment_intent_id(self, value):
        """Validar que el payment intent existe en la base de datos"""
        if not Pago.objects.filter(stripe_payment_intent_id=value).exists():
            raise serializers.ValidationError("No se encontró un pago asociado a este Payment Intent")
        return value


class StripeRefundSerializer(serializers.Serializer):
    """Serializer para reembolsar un pago de Stripe"""
    
    pago_id = serializers.IntegerField()
    monto = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        help_text="Monto a reembolsar. Si no se proporciona, se reembolsa el total"
    )
    razon = serializers.CharField(
        max_length=500,
        required=False,
        help_text="Razón del reembolso"
    )
    
    def validate_pago_id(self, value):
        """Validar que el pago existe y puede ser reembolsado"""
        try:
            pago = Pago.objects.get(id=value)
            if not pago.puede_reembolsar():
                raise serializers.ValidationError("Este pago no puede ser reembolsado")
        except Pago.DoesNotExist:
            raise serializers.ValidationError("El pago no existe")
        return value
    
    def validate_monto(self, value):
        """Validar que el monto de reembolso no exceda el monto original"""
        if value:
            pago_id = self.initial_data.get('pago_id')
            if pago_id:
                pago = Pago.objects.get(id=pago_id)
                if value > pago.monto:
                    raise serializers.ValidationError("El monto de reembolso no puede ser mayor al monto original")
        return value
