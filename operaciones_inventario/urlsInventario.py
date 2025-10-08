from rest_framework.routers import DefaultRouter
from .viewsInventario import InventarioViewSet

router = DefaultRouter()
router.register(r'inventarios', InventarioViewSet, basename='inventario')

urlpatterns = router.urls
