# personal_admin/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    UserViewSet, 
    GroupAuxViewSet, 
    CargoViewSet, 
    UserRegistrationView, 
    LogoutView, 
    RoleViewSet, 
    PermissionViewSet,
    EmpleadoViewSet, 
    CSRFTokenView, 
    ClienteProfileUpdateView, 
    EmpleadoProfileUpdateView,
    ChangePasswordView, 
    CustomTokenObtainPairView
)

app_name = 'personal_admin'  # ← añadido para evitar conflictos de nombres

router = DefaultRouter()

# Rutas de tus compañeros
router.register(r'users', UserViewSet, basename='user')
router.register(r'cargos', CargoViewSet, basename='cargo')
router.register(r'empleados', EmpleadoViewSet, basename='empleado')

# Rutas para Roles y Permisos
router.register(r'groupsAux', RoleViewSet, basename='role')
router.register(r'permissions', PermissionViewSet, basename='permission')


urlpatterns = [
    path('', include(router.urls)),
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path("auth/token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("csrf/", CSRFTokenView.as_view(), name="csrf-token"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('cliente/profile/', ClienteProfileUpdateView.as_view(), name='cliente-profile-update'),
    path('empleado/profile/', EmpleadoProfileUpdateView.as_view(), name='empleado-profile-update'),
]


