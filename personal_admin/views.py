# personal_admin/views.py
from rest_framework import viewsets
from django.contrib.auth.models import User, Group
from .models import Cargo

from .serializers.serializers_user import UserSerializer, GroupAuxSerializer
from .serializers.serializers_cargo import CargoSerializer
from .serializers.serializers_rol import RoleSerializer  # <- tu serializer para roles


# ---- ViewSets de tus compañeros ----
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class GroupAuxViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupAuxSerializer


class CargoViewSet(viewsets.ModelViewSet):
    queryset = Cargo.objects.all()
    serializer_class = CargoSerializer


# ---- Tu nuevo ViewSet para Roles ----
class RoleViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all().order_by('name')
    serializer_class = RoleSerializer
