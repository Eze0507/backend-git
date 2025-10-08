from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsVehiculos import VehiculoViewSet

router = DefaultRouter()
router.register(r'vehiculos', VehiculoViewSet, basename='vehiculo')

urlpatterns = [
    path('', include(router.urls)),
]
