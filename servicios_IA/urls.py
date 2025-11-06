# servicios_IA/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AlprScanView
from .viewsReportes import ReporteViewSet

# Router para ViewSets
router = DefaultRouter()
router.register(r'reportes', ReporteViewSet, basename='reporte')

urlpatterns = [
    path("alpr/", AlprScanView.as_view(), name="alpr-scan"),
    path("", include(router.urls)),
from .views_chatbot import GeminiChatView


urlpatterns = [
    path("alpr/", AlprScanView.as_view(), name="alpr-scan"),
    path("chatbot/", GeminiChatView.as_view(), name="chatbot"),
]
