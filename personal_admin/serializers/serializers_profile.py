# serializers_profile.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from clientes_servicios.models import Cliente

User = get_user_model()

class ProfileUpdateSerializer(serializers.ModelSerializer):
    # Campos que quieres permitir que el usuario actualice
    username = serializers.CharField(source='user.username', required=False)
    email = serializers.EmailField(source='user.email', required=False)

    class Meta:
        model = Cliente
        fields = [
            'nombre', 'apellido', 'direccion', 'telefono', 
            'tipo_cliente', 'username', 'email'
        ]
    
    def update(self, instance, validated_data):
        # Manejar la actualización de los campos del User
        user_data = validated_data.pop('user', {})
        user_instance = instance.usuario
        
        if user_data:
            for attr, value in user_data.items():
                setattr(user_instance, attr, value)
            user_instance.save()
            
        # Manejar la actualización de los campos del Cliente
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance