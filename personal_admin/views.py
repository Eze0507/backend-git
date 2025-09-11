from django.shortcuts import render
from rest_framework import viewsets
from .serializers.serializers_user import UserSerializer, GroupAuxSerializer
from django.contrib.auth.models import User, Group

from .models import Cargo
from .serializers.serializers_cargo import CargoSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class GroupAuxViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupAuxSerializer


class CargoViewSet(viewsets.ModelViewSet):
	queryset = Cargo.objects.all()
	serializer_class = CargoSerializer