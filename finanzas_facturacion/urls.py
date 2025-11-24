from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PagoViewSet,
    CreatePaymentIntentOrden,
    VerifyPaymentIntentOrden,
    ConfirmPaymentAutoOrden,
    ConfirmPaymentWithCardOrden
)
from .viewsFactProv import FacturaProveedorViewSet
from .viewsDetallesFactProv import DetalleFacturaProveedorViewSet
from .views_export import ExportarPagoPDFView, ExportarPagoExcelView

router = DefaultRouter()
router.register(r'pagos', PagoViewSet, basename='pago')
router.register(r'facturas-proveedor', FacturaProveedorViewSet, basename='factura-proveedor')
router.register(r'detalles-factura-proveedor', DetalleFacturaProveedorViewSet, basename='detalle-factura-proveedor')

urlpatterns = [
    # Stripe Endpoints (deben ir ANTES del router)
    path('pagos/create-payment-intent/', CreatePaymentIntentOrden.as_view(), name='create-payment-intent'),
    path('pagos/confirm-payment-auto/', ConfirmPaymentAutoOrden.as_view(), name='confirm-payment-auto'),
    path('pagos/confirm-payment-with-card/', ConfirmPaymentWithCardOrden.as_view(), name='confirm-payment-with-card'),
    path('pagos/verify-payment/', VerifyPaymentIntentOrden.as_view(), name='verify-payment'),
    path('pagos/confirm-payment/', VerifyPaymentIntentOrden.as_view(), name='confirm-payment'),  # Alias
    
    # Export endpoints
    path('pagos/<int:pk>/export/pdf/', ExportarPagoPDFView.as_view(), name='exportar-pago-pdf'),
    path('pagos/<int:pk>/export/excel/', ExportarPagoExcelView.as_view(), name='exportar-pago-excel'),
    
    # Router de pagos (CRUD básico)
    path('', include(router.urls)),
]
