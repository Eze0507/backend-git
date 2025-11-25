from rest_framework import serializers
from django.db import IntegrityError
from .models_device_token import DeviceToken


class DeviceTokenSerializer(serializers.ModelSerializer):
    """Serializer para registrar tokens FCM de dispositivos"""
    
    class Meta:
        model = DeviceToken
        fields = ['id', 'token', 'platform', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_active']
    
    def create(self, validated_data):
        """
        Crea o actualiza el token si ya existe.
        Si el token está asociado a otro usuario, lo reasigna al usuario actual.
        """
        user = self.context['request'].user
        token = validated_data.get('token')
        platform = validated_data.get('platform', 'android')
        
        # Primero, intentar encontrar y actualizar el token existente
        device_token = DeviceToken.objects.filter(token=token).first()
        
        if device_token:
            # Token existe, actualizar sus datos
            device_token.user = user
            device_token.platform = platform
            device_token.is_active = True
            device_token.save()
            return device_token
        
        # Token no existe, crear uno nuevo
        try:
            device_token = DeviceToken.objects.create(
                user=user,
                token=token,
                platform=platform,
                is_active=True
            )
        except IntegrityError:
            # Race condition: otro proceso creó el token justo antes
            # Intentar obtenerlo y actualizarlo
            device_token = DeviceToken.objects.get(token=token)
            device_token.user = user
            device_token.platform = platform
            device_token.is_active = True
            device_token.save()
        
        return device_token
