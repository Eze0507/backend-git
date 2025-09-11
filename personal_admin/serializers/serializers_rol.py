# personal_admin/serializers/serializers_role.py
from rest_framework import serializers
from django.contrib.auth.models import Group

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name'] #id para identificar cada rol con la API
