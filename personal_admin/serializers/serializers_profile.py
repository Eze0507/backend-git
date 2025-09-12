# serializers_profile.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from clientes_servicios.models import Cliente
from personal_admin.models import Empleado
User = get_user_model()

class ProfileUpdateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', required=False)
    email = serializers.EmailField(source='user.email', required=False)

    class Meta:
        model = Cliente
        fields = [
            'nombre', 'apellido', 'direccion', 'telefono', 
            'tipo_cliente', 'username', 'email'
        ]
    
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
    username = serializers.CharField(source='usuario.username', required=False)
    email = serializers.EmailField(source='usuario.email', required=False)

    class Meta:
        model = Empleado
        fields = [
            'nombre', 'apellido', 'direccion', 'telefono', 
            'ci', 'username', 'email'
        ]
    
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