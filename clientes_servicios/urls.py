"""""
from django.urls import path
from . import views
from django.http import HttpResponse

#def test_view(request):
#    return HttpResponse("Rutas de clientes funcionando 🚀")

urlpatterns = [
#    path('test/', test_view),
    path('clientes/', views.cliente_list, name='cliente_list'),
    path('clientes/<int:pk>/', views.cliente_detail, name='cliente_detail'),
    path('clientes/nuevo/', views.cliente_create, name='cliente_create'),
    path('clientes/<int:pk>/editar/', views.cliente_edit, name='cliente_edit'),
    path('clientes/<int:pk>/eliminar/', views.cliente_delete, name='cliente_delete'),
]
"""
from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import ClienteViewSet, CitaViewSet
from .views_cita import CitaClienteViewSet, CalendarioEmpleadoView

router = DefaultRouter()
router.register(r'clientes', ClienteViewSet, basename='cliente')
router.register(r'citas', CitaViewSet, basename='cita')
router.register(r'citas-cliente', CitaClienteViewSet, basename='cita-cliente')

# IMPORTANTE: La ruta manual debe ir ANTES del router para que tenga prioridad
urlpatterns = [
    # Endpoint independiente para calendario (fuera del ViewSet para evitar 302)
    path('citas-cliente/empleado/<int:empleado_id>/calendario/', CalendarioEmpleadoView.as_view(), name='calendario-empleado'),
] + router.urls



