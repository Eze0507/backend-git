from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsServicios import AreaViewSet, CategoriaViewSet, ServicioViewSet

# Crear router para los servicios
router = DefaultRouter()
router.register(r'areas', AreaViewSet, basename='area')
router.register(r'categorias', CategoriaViewSet, basename='categoria')
router.register(r'servicios', ServicioViewSet, basename='servicio')

# URLs de servicios
urlpatterns = [
    path('', include(router.urls)),
]
