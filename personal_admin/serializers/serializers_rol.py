from rest_framework import serializers
from django.contrib.auth.models import Group, Permission

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'name', 'codename']

class RoleSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)
    permission_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Permission.objects.all(),
        write_only=True,
        source='permissions'  # se asignan a la relación Group.permissions
    )

    class Meta:
        model = Group
        fields = ['id', 'name', 'permissions', 'permission_ids']

    def update(self, instance, validated_data):
        permission_data = validated_data.pop('permissions', None)

        # agregar nuevos permisos sin eliminar los existentes
        if permission_data:
            for perm in permission_data:
                instance.permissions.add(perm)

        return super().update(instance, validated_data)
