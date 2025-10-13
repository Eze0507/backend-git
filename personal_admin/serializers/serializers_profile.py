# serializers_profile.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from clientes_servicios.models import Cliente
from personal_admin.models import Empleado
User = get_user_model()

class ProfileReadSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='usuario.username', read_only=True)
    email = serializers.EmailField(source='usuario.email', read_only=True)

    class Meta:
        model = Empleado
        fields = [
            'id', 'nombre', 'apellido', 'direccion', 'telefono', 
            'ci', 'username', 'email'
        ]
        read_only_fields = ['id', 'ci']

class ProfileUpdateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='usuario.username', required=False, allow_blank=True)
    email = serializers.EmailField(source='usuario.email', required=False, allow_blank=True)

    class Meta:
        model = Cliente
        fields = [
            'nombre', 'apellido', 'direccion', 'telefono', 
            'tipo_cliente', 'username', 'email'
        ]
    
    def to_representation(self, instance):
        """Personalizar la representación para manejar casos donde no hay usuario"""
        data = super().to_representation(instance)
        
        # Si no hay usuario asociado, establecer valores por defecto
        if not instance.usuario:
            data['username'] = 'No especificado'
            data['email'] = 'No especificado'
        else:
            data['username'] = instance.usuario.username or 'No especificado'
            data['email'] = instance.usuario.email or 'No especificado'
            
        # Asegurar que los campos requeridos no estén vacíos
        data['nombre'] = instance.nombre or 'No especificado'
        data['apellido'] = instance.apellido or 'No especificado'
        data['direccion'] = instance.direccion or 'No especificado'
        data['telefono'] = instance.telefono or 'No especificado'
        
        return data
    
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        user_instance = instance.usuario
        
        if user_data:
            for attr, value in user_data.items():
                setattr(user_instance, attr, value)
            user_instance.save()
            
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance

class EmpleadoProfileUpdateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='usuario.username', required=False, allow_blank=True)
    email = serializers.EmailField(source='usuario.email', required=False, allow_blank=True)

    class Meta:
        model = Empleado
        fields = [
            'nombre', 'apellido', 'direccion', 'telefono', 
            'ci', 'username', 'email'
        ]
    
    def to_representation(self, instance):
        """Personalizar la representación para manejar casos donde no hay usuario"""
        data = super().to_representation(instance)
        
        # Si no hay usuario asociado, establecer valores por defecto
        if not instance.usuario:
            data['username'] = 'No especificado'
            data['email'] = 'No especificado'
        else:
            data['username'] = instance.usuario.username or 'No especificado'
            data['email'] = instance.usuario.email or 'No especificado'
            
        # Asegurar que los campos requeridos no estén vacíos
        data['nombre'] = instance.nombre or 'No especificado'
        data['apellido'] = instance.apellido or 'No especificado'
        data['direccion'] = instance.direccion or 'No especificado'
        data['telefono'] = instance.telefono or 'No especificado'
        data['ci'] = instance.ci or 'No especificado'
        
        return data
    
    def update(self, instance, validated_data):
        user_data = validated_data.pop('usuario', {})
        user_instance = instance.usuario
        
        if user_data and user_instance:
            for attr, value in user_data.items():
                setattr(user_instance, attr, value)
            user_instance.save()
            
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance