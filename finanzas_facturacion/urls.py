from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsPagos import PagoViewSet
from .viewsFactProv import FacturaProveedorViewSet
from .viewsDetallesFactProv import DetalleFacturaProveedorViewSet

router = DefaultRouter()
router.register(r'pagos', PagoViewSet, basename='pago')
router.register(r'facturas-proveedor', FacturaProveedorViewSet, basename='factura-proveedor')
router.register(r'detalles-factura-proveedor', DetalleFacturaProveedorViewSet, basename='detalle-factura-proveedor')

urlpatterns = [
    path('', include(router.urls)),
]
