from rest_framework import serializers
from ..models import Bitacora
from django.contrib.auth.models import User

class BitacoraSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source='usuario.username', read_only=True)
    usuario_email = serializers.CharField(source='usuario.email', read_only=True)
    
    class Meta:
        model = Bitacora
        fields = [
            'id',
            'usuario',
            'usuario_nombre', 
            'usuario_email',
            'accion',
            'modulo',
            'descripcion',
            'ip_address',
            'fecha_accion'
        ]
        read_only_fields = ['id', 'fecha_accion']
