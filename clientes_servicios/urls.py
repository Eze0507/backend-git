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
from .views import ClienteViewSet

router = DefaultRouter()
router.register(r'clientes', ClienteViewSet, basename='cliente')

urlpatterns = router.urls



