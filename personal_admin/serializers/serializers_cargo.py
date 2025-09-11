from rest_framework import serializers
from ..models import Cargo

class CargoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cargo
        fields = '__all__'

def validate_nombre(self, value):
        if not value.strip():
            raise serializers.ValidationError("El nombre no puede estar vacío.")
        return value

def validate_sueldo(self, value):
        if value <= 0:
            raise serializers.ValidationError("El sueldo debe ser mayor a cero.")
        return value

