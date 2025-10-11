from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsVehiculos import VehiculoViewSet
from .viewsArea import AreaViewSet
from .viewsItem import ItemViewSet

router = DefaultRouter()
router.register(r'vehiculos', VehiculoViewSet, basename='vehiculo')
router.register(r'areas', AreaViewSet, basename='area')
router.register(r'items', ItemViewSet, basename='item')

urlpatterns = [
    path('', include(router.urls)),
]
