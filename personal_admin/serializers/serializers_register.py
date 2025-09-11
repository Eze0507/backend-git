from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.db import transaction

class UserRegistrationSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True)
    username = serializers.CharField(
        validators=[
            UniqueValidator(queryset=User.objects.all(), message="Este nombre de usuario ya está en uso.")
        ]
    )
    email = serializers.EmailField(
        validators=[
            UniqueValidator(queryset=User.objects.all(), message="Este email ya está registrado.")
        ]
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, attrs):
        # 1. Validar que las contraseñas coincidan
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden."})
        # 2. Validar contraseña usando validadores de Django
        try:
            validate_password(attrs['password'])
        except ValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})
        
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        with transaction.atomic():
            try:
                cliente_group = Group.objects.get(name='cliente')
            except Group.DoesNotExist:
                raise serializers.ValidationError({
                    "non_field_errors": ["El grupo 'cliente' no existe. Por favor, créalo primero."]
                })
            user = User.objects.create_user(**validated_data)
            user.groups.add(cliente_group)
        return user
