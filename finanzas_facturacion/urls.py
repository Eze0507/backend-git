from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PagoViewSet,
    CreatePaymentIntentOrden,
    VerifyPaymentIntentOrden
)
from .viewsFactProv import FacturaProveedorViewSet
from .viewsDetallesFactProv import DetalleFacturaProveedorViewSet

router = DefaultRouter()
router.register(r'pagos', PagoViewSet, basename='pago')
router.register(r'facturas-proveedor', FacturaProveedorViewSet, basename='factura-proveedor')
router.register(r'detalles-factura-proveedor', DetalleFacturaProveedorViewSet, basename='detalle-factura-proveedor')

urlpatterns = [
    # Stripe Endpoints (deben ir ANTES del router)
    path('pagos/create-payment-intent/', CreatePaymentIntentOrden.as_view(), name='create-payment-intent'),
    path('pagos/confirm-payment/', VerifyPaymentIntentOrden.as_view(), name='confirm-payment'),
    
    # Router de pagos (CRUD básico)
    path('', include(router.urls)),
]
