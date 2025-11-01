from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from .viewsVehiculos import VehiculoViewSet
from .viewsArea import AreaViewSet
from .viewsItem import ItemViewSet
from .viewsOrdenTrabajo import OrdenTrabajoViewSet, DetalleOrdenTrabajoViewSet, NotaOrdenTrabajoViewSet, TareaOrdenTrabajoViewSet, inventarioVehiculoViewSet, inspeccionViewSet, PruebaRutaViewSet, AsignacionTecnicoViewSet, ImagenOrdenTrabajoViewSet
from .viewsPresupuesto import PresupuestoViewSet, DetallePresupuestoViewSet
from .viewsProveedor import ProveedorViewSet

router = DefaultRouter()
router.register(r'vehiculos', VehiculoViewSet, basename='vehiculo')
router.register(r'areas', AreaViewSet, basename='area')
router.register(r'items', ItemViewSet, basename='item')
router.register(r'ordenes', OrdenTrabajoViewSet)
ordenes_router = routers.NestedDefaultRouter(router, r'ordenes', lookup='orden')
ordenes_router.register(r'detalles', DetalleOrdenTrabajoViewSet, basename='orden-detalles')
router.register(r'presupuestos', PresupuestoViewSet, basename='presupuesto')
router.register(r'detalles-presupuesto', DetallePresupuestoViewSet, basename='detalle-presupuesto')
ordenes_router.register(r'notas', NotaOrdenTrabajoViewSet, basename='orden-notas')
ordenes_router.register(r'tareas', TareaOrdenTrabajoViewSet, basename='orden-tareas')
ordenes_router.register(r'inventario', inventarioVehiculoViewSet, basename='orden-inventario')
ordenes_router.register(r'inspecciones', inspeccionViewSet, basename='orden-inspecciones')
ordenes_router.register(r'pruebas', PruebaRutaViewSet, basename='orden-pruebas-ruta')
ordenes_router.register(r'asignaciones', AsignacionTecnicoViewSet, basename='orden-asignaciones-tecnicos')
ordenes_router.register(r'imagenes', ImagenOrdenTrabajoViewSet, basename='orden-imagenes')
router.register(r'proveedores', ProveedorViewSet, basename='proveedor')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(ordenes_router.urls)),
]
