from rest_framework import serializers
from ..models import Cliente
from django.contrib.auth import get_user_model

User = get_user_model()

class ClienteSerializer(serializers.ModelSerializer):
    usuario_info = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Cliente
        fields = [
            'id', 'nombre', 'apellido', 'nit', 'telefono',
            'direccion', 'tipo_cliente', 'activo', 'usuario', 'usuario_info'
        ]
        read_only_fields = ('id',)  # solo el ID es readonly

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si es actualización, no obligar a llenar nit ni teléfono
        if self.instance:
            self.fields['nit'].required = False
            self.fields['telefono'].required = False

    def get_usuario_info(self, obj):
        if not obj.usuario:
            return None
        return {
            'id': obj.usuario.id,
            'username': getattr(obj.usuario, 'username', None),
            'email': getattr(obj.usuario, 'email', None),
        }

    # -------- VALIDACIONES --------
    def validate_nombre(self, value):
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("El nombre debe tener al menos 2 caracteres.")
        return value

    def validate_apellido(self, value):
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("El apellido debe tener al menos 2 caracteres.")
        return value

    def validate_telefono(self, value):
        value = value.strip()
        qs = Cliente.objects.filter(telefono=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Este teléfono ya está registrado.")
        if not value.isdigit():
            raise serializers.ValidationError("El teléfono solo puede contener números.")
        return value

    def validate_nit(self, value):
        value = value.strip()
        qs = Cliente.objects.filter(nit=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Este NIT ya está registrado.")
        return value

    # -------- CREATE & UPDATE --------
    def create(self, validated_data):
        return Cliente.objects.create(**validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)
