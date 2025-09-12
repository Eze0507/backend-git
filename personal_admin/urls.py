# personal_admin/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import UserViewSet, GroupAuxViewSet, CargoViewSet, UserRegistrationView, LogoutView, RoleViewSet, EmpleadoViewSet

app_name = 'personal_admin'  # ← añadido para evitar conflictos de nombres

router = DefaultRouter()

# Rutas de tus compañeros
router.register(r'users', UserViewSet, basename='user')
router.register(r'groupsAux', GroupAuxViewSet, basename='groupAux')
router.register(r'cargos', CargoViewSet, basename= 'cargo')
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'empleados', EmpleadoViewSet, basename='empleado')


urlpatterns = [
    path('', include(router.urls)),
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]


