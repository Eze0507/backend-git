# En: personal_admin/serializers/serializers_user.py (o donde lo vayas a poner)

from rest_framework import serializers
from django.contrib.auth.models import User, Group
from django.db import transaction
from personal_admin.models_saas import Tenant, UserProfile # Asegúrate de importar tus modelos

class TallerRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer para el formulario público de registro de un NUEVO Taller.
    Crea el Tenant, el User (propietario) y el UserProfile.
    """
    # Pedimos el nombre del taller como un campo extra
    nombre_taller = serializers.CharField(max_length=100, write_only=True)
    
    class Meta:
        model = User
        # Pedimos los campos básicos del User + el nombre_taller
        fields = ['username', 'email', 'password', 'nombre_taller']
        extra_kwargs = {
            'password': {'write_only': True},
            # Hacemos el email opcional si así lo decides
            'email': {'required': False} 
        }

    def validate_username(self, value):
        # (Aquí puedes poner tus validaciones de username)
        if " " in value:
            raise serializers.ValidationError("El nombre de usuario no puede tener espacios.")
        return value

    def validate_nombre_taller(self, value):
        # Comprobar que el nombre del taller no exista
        if Tenant.objects.filter(nombre_taller=value).exists():
            raise serializers.ValidationError("Un taller con este nombre ya existe.")
        return value

    @transaction.atomic # Si algo falla, revierte todos los cambios
    def create(self, validated_data):
        # 1. Sacamos los datos
        nombre_taller = validated_data.pop('nombre_taller')
        
        # (Usamos el email "falso" que discutimos si no viene uno)
        if 'email' not in validated_data or not validated_data['email']:
            validated_data['email'] = f"{validated_data['username']}@internal-user.com"
        
        # 2. Creamos el User (el propietario)
        user_propietario = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        
        # 3. Creamos el Tenant (el taller) y lo vinculamos
        nuevo_taller = Tenant.objects.create(
            nombre_taller=nombre_taller,
            propietario=user_propietario # Asignamos el "título de propiedad"
        )
        
        # 4. Creamos el UserProfile (la "llave" del propietario)
        #    (Esto reemplaza la lógica del signal, que quitamos)
        UserProfile.objects.create(
            usuario=user_propietario,
            tenant=nuevo_taller
        )
        
        # 5. (Opcional) Asignar al grupo 'administrador'
        try:
            admin_group = Group.objects.get(name='administrador')
            user_propietario.groups.add(admin_group)
        except Group.DoesNotExist:
            print("Advertencia: No se encontró el grupo 'administrador' para el nuevo propietario.")
            
        return user_propietario