# En: personal_admin/serializers/serializers_user.py (o donde prefieras)
from rest_framework import serializers
from django.contrib.auth.models import User, Group
from clientes_servicios.models import Cliente # Importa tu modelo Cliente
from django.db import transaction
from personal_admin.models_saas import Tenant, UserProfile # Asegúrate de importar tus

class ClienteRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer para el formulario público de registro de un NUEVO Cliente
    usando un código de invitación.
    """
    # Pedimos los campos extra
    codigo_invitacion = serializers.CharField(max_length=50, write_only=True)
    nombre = serializers.CharField(max_length=100, write_only=True)
    apellido = serializers.CharField(max_length=100, write_only=True, required=False)
    
    # -----------------------------------------------------------------
    # NUEVO: Añadir el campo NIT, ya que es requerido por tu modelo Cliente
    # -----------------------------------------------------------------
    nit = serializers.CharField(max_length=20, write_only=True)
    # -----------------------------------------------------------------

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'nombre', 'apellido', 'nit', 'codigo_invitacion']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': False} # (Mantenemos el email opcional en User)
        }

    def validate_codigo_invitacion(self, value):
        # Comprobamos si el código de invitación existe
        if not Tenant.objects.filter(codigo_invitacion=value).exists():
            raise serializers.ValidationError("El código de invitación no es válido o ha expirado.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        # 1. Sacamos los datos extra
        codigo = validated_data.pop('codigo_invitacion')
        nombre_cliente = validated_data.pop('nombre')
        apellido_cliente = validated_data.pop('apellido', '')
        nit_cliente = validated_data.pop('nit') # <-- NUEVO: Obtener el NIT
        
        # 2. Buscamos el Tenant
        try:
            tenant = Tenant.objects.get(codigo_invitacion=codigo)
        except Tenant.DoesNotExist:
            raise serializers.ValidationError({"codigo_invitacion": "El código de invitación no es válido."})
        
        # 3. Creamos el User (el cliente)
        if 'email' not in validated_data or not validated_data['email']:
            validated_data['email'] = f"{validated_data['username']}@internal-user.com"
            
        user_cliente = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        
        # 4. Creamos el UserProfile (la "llave" del cliente)
        UserProfile.objects.create(
            usuario=user_cliente,
            tenant=tenant
        )
        
        # 5. Creamos el modelo Cliente (el "perfil" del cliente)
        Cliente.objects.create(
            usuario=user_cliente,
            tenant=tenant,
            nombre=nombre_cliente,
            apellido=apellido_cliente,
            nit=nit_cliente # <-- NUEVO: Guardar el NIT
        )
        
        # 6. (Opcional) Asignar al grupo 'cliente'
        try:
            cliente_group = Group.objects.get(name='cliente')
            user_cliente.groups.add(cliente_group)
        except Group.DoesNotExist:
            print("Advertencia: No se encontró el grupo 'cliente'.")
            
        return user_cliente