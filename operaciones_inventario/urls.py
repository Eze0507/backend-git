from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from .viewsVehiculos import VehiculoViewSet
from .viewsArea import AreaViewSet
from .viewsItem import ItemViewSet
from .viewsOrdenTrabajo import OrdenTrabajoViewSet, DetalleOrdenTrabajoViewSet
from .viewsPresupuesto import PresupuestoViewSet, DetallePresupuestoViewSet

router = DefaultRouter()
router.register(r'vehiculos', VehiculoViewSet, basename='vehiculo')
router.register(r'areas', AreaViewSet, basename='area')
router.register(r'items', ItemViewSet, basename='item')
router.register(r'ordenes', OrdenTrabajoViewSet)
ordenes_router = routers.NestedDefaultRouter(router, r'ordenes', lookup='orden')
ordenes_router.register(r'detalles', DetalleOrdenTrabajoViewSet, basename='orden-detalles')
router.register(r'presupuestos', PresupuestoViewSet, basename='presupuesto')
router.register(r'detalles-presupuesto', DetallePresupuestoViewSet, basename='detalle-presupuesto')


urlpatterns = [
    path('', include(router.urls)),
    path('', include(ordenes_router.urls)),
]
