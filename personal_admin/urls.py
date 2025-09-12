# personal_admin/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, GroupAuxViewSet, CargoViewSet, UserRegistrationView, LogoutView, RoleViewSet, ClienteProfileUpdateView
from .views import ChangePasswordView

app_name = 'personal_admin'  # ← añadido para evitar conflictos de nombres

router = DefaultRouter()

# Rutas de tus compañeros
router.register(r'users', UserViewSet, basename='user')
router.register(r'groupsAux', GroupAuxViewSet, basename='groupAux')
router.register(r'cargos', CargoViewSet, basename= 'cargo')
router.register(r'roles', RoleViewSet, basename='role')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ClienteProfileUpdateView.as_view(), name='cliente_profile_update'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
]


