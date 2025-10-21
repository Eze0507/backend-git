from rest_framework import serializers
from ..models import Cliente
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email']


class UserPKOrNestedField(serializers.PrimaryKeyRelatedField):
    """Permite enviar `usuario` como ID (int) o como objeto {id: X}.

    También acepta null/"" para dejarlo vacío.
    """
    def to_internal_value(self, data):
        # Aceptar objetos con {id: ...} o {pk: ...}
        if isinstance(data, dict):
            data = data.get('id') or data.get('pk')

        # Normalizar vacíos
        if data in (None, ""):
            if self.allow_null:
                return None
            self.fail('required')

        return super().to_internal_value(data)


class ClienteSerializer(serializers.ModelSerializer):
    usuario_info = serializers.SerializerMethodField(read_only=True)
    # Aceptar ID o objeto con id
    usuario = UserPKOrNestedField(queryset=User.objects.all(), required=False, allow_null=True)

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
        # Apellido es opcional; si viene vacío, permitirlo
        if value == "":
            return value
        if len(value) < 2:
            raise serializers.ValidationError("El apellido debe tener al menos 2 caracteres si se proporciona.")
        return value

    def validate_telefono(self, value):
        value = value.strip()
        # Teléfono es opcional
        if value == "":
            return value
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
        # 'usuario' ahora es un User o None directamente desde validated_data
        return Cliente.objects.create(**validated_data)

    def update(self, instance, validated_data):
        # Permite actualizar 'usuario' pasando el ID o dejarlo igual
        return super().update(instance, validated_data)
