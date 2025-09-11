from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, GroupAuxViewSet, CargoViewSet

router = DefaultRouter()

router.register(r'users', UserViewSet, basename='user')
router.register(r'groupsAux', GroupAuxViewSet, basename='groupAux')
urlpatterns = [
    path('', include(router.urls)),
]

router.register(r'cargos', CargoViewSet)
urlpatterns = [
    path('', include(router.urls)),
]