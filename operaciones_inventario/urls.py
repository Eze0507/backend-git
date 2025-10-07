from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MarcaViewSet
from .urlsServicios import urlpatterns as servicios_urls

router = DefaultRouter()
router.register(r'marcas', MarcaViewSet, basename='marca')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(servicios_urls)),
]
