from rest_framework import serializers
from django.contrib.auth.models import User
from personal_admin.models import Empleado, Cargo  # Asegúrate de tener el modelo Empleado creado

class CargoMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cargo
        fields = ("id", "nombre", "sueldo")

class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "is_active")

class EmpleadoReadSerializer(serializers.ModelSerializer):
    cargo = CargoMiniSerializer(read_only=True)
    usuario = UserMiniSerializer(read_only=True)

    class Meta:
        model = Empleado
        fields = (
            "id", "nombre", "apellido", "ci", "direccion", "telefono", "sexo",
            "sueldo", "estado", "fecha_registro", "fecha_actualizado",
            "cargo", "usuario"
        )

class EmpleadoWriteSerializer(serializers.ModelSerializer):
    cargo_id = serializers.PrimaryKeyRelatedField(
        queryset=Cargo.objects.all(), source="cargo", write_only=True
    )
    usuario_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="usuario",
        write_only=True, allow_null=True, required=False
    )

    class Meta:
        model = Empleado
        fields = (
            "nombre", "apellido", "ci", "direccion", "telefono", "sexo",
            "sueldo", "estado", "cargo_id", "usuario_id"
        )

    def validate(self, attrs):
        usuario = attrs.get("usuario")
        if usuario and hasattr(usuario, "empleado") and self.instance is None:
            raise serializers.ValidationError({"usuario_id": "Este usuario ya está asociado a un empleado."})
        sueldo = attrs.get("sueldo")
        if sueldo is not None and sueldo < 0:
            raise serializers.ValidationError({"sueldo": "El sueldo no puede ser negativo."})
        return attrs
