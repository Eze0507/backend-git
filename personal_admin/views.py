from django.shortcuts import render
from rest_framework import viewsets
from .serializers.serializers_user import UserSerializer, GroupAuxSerializer
from django.contrib.auth.models import User, Group

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
# Create your views here.

class GroupAuxViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupAuxSerializer
