# personal_admin/urls.py
from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views_device_token import register_device_token, unregister_device_token

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
    CustomTokenObtainPairView,
    BitacoraViewSet,
    UserProfileView,
    MeView,
    TallerRegistrationView,
    TenantProfileView,
    ClienteRegistrationView,
    DashboardAdminView,
    DashboardEmpleadoView,
    AsistenciaViewSet,
    AsistenciaReporteMensualView,
    MarcarAsistenciaView,
    MiAsistenciaView,
    MiHistorialAsistenciaView,
    DiagnosticoAsistenciasView,
    CreateEmbeddedSubscription,
    ActivarSuscripcionView
)
from .views_nomina import NominaViewSet, DetalleNominaViewSet

app_name = 'personal_admin'  # ← añadido para evitar conflictos de nombres

router = DefaultRouter()

# Rutas de tus compañeros
router.register(r'users', UserViewSet, basename='user')
router.register(r'cargos', CargoViewSet, basename='cargo')
router.register(r'empleados', EmpleadoViewSet, basename='empleado')

# Rutas para Roles y Permisos
router.register(r'groupsAux', RoleViewSet, basename='role')
router.register(r'permissions', PermissionViewSet, basename='permission')

# Ruta para Bitácora
router.register(r'bitacora', BitacoraViewSet, basename='bitacora')

# Ruta para Asistencia
router.register(r'asistencias', AsistenciaViewSet, basename='asistencia')

# Rutas para Nómina
router.register(r'nominas', NominaViewSet, basename='nomina')
router.register(r'detalle-nomina', DetalleNominaViewSet, basename='detalle-nomina')


urlpatterns = [
    path('', include(router.urls)),
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path("auth/token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("csrf/", CSRFTokenView.as_view(), name="csrf-token"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),  # Nueva vista unificada
    path('cliente/profile/', ClienteProfileUpdateView.as_view(), name='cliente-profile-update'),
    path('empleado/profile/', EmpleadoProfileUpdateView.as_view(), name='empleado-profile-update'),
    path('auth/me/', MeView.as_view(), name='me'),
    path('taller/', TallerRegistrationView.as_view(), name='register-taller'),
    path('cliente-registro/', ClienteRegistrationView.as_view(), name='register-cliente'),
    path('perfil-taller/', TenantProfileView.as_view(), name='tenant-profile'),
    path('dashboard/admin/', DashboardAdminView.as_view(), name='dashboard-admin'),
    path('dashboard/empleado/', DashboardEmpleadoView.as_view(), name='dashboard-empleado'),
    path('asistencia/marcar/', MarcarAsistenciaView.as_view(), name='asistencia-marcar'),
    path('asistencia/mi-asistencia/', MiAsistenciaView.as_view(), name='mi-asistencia'),
    path('asistencia/mi-historial/', MiHistorialAsistenciaView.as_view(), name='mi-historial-asistencia'),
    path('asistencia/reporte-mensual/', AsistenciaReporteMensualView.as_view(), name='asistencia-reporte-mensual'),
    path('asistencia/diagnostico/', DiagnosticoAsistenciasView.as_view(), name='diagnostico-asistencias'),
    path('device-token/register/', register_device_token, name='device-token-register'),
    path('device-token/unregister/', unregister_device_token, name='device-token-unregister'),
    path('crear-suscripcion-embedded/', CreateEmbeddedSubscription.as_view(), name='create-subscription-session'),
    path('activar-suscripcion/', ActivarSuscripcionView.as_view(), name='activar-suscripcion'),
]


