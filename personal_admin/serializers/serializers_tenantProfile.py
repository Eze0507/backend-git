# En: personal_admin/serializers/serializers_tenant.py (o como lo llames)

from rest_framework import serializers
from personal_admin.models_saas import Tenant

class TenantProfileSerializer(serializers.ModelSerializer):
    """
    Serializer para que el Propietario vea y actualice
    la información de su propio Taller (Tenant).
    """
    
    # Campo de solo lectura para mostrar quién es el propietario
    propietario_username = serializers.CharField(
        source='propietario.username', 
        read_only=True
    )
    
    class Meta:
        model = Tenant
        
        # 1. Lista todos los campos que el propietario debe VER
        fields = [
            'id',
            'nombre_taller', 
            'ubicacion', 
            'telefono', 
            'horarios', 
            'email_contacto', 
            'logo',
            'codigo_invitacion',
            'propietario_username',
            'activo',
            'fecha_creacion',
        ]
        
        # 2. Bloquea los campos que NO debe poder editar
        read_only_fields = [
            'id', 
            'codigo_invitacion',      # El código se genera solo, no se edita
            'propietario_username',
            'activo',                 # El estado de 'activo' lo manejas tú (pagos)
            'fecha_creacion',
        ]