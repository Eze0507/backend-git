from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, GroupAuxViewSet, CargoViewSet, UserRegistrationView, LogoutView

router = DefaultRouter()

router.register(r'users', UserViewSet, basename='user')
router.register(r'groupsAux', GroupAuxViewSet, basename='groupAux')
router.register(r'cargos', CargoViewSet, basename= 'cargo')
urlpatterns = [
    path('', include(router.urls)),
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
]


