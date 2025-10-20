# servicios_IA/urls.py
from django.urls import path
from .views import AlprScanView

urlpatterns = [
    path("alpr/", AlprScanView.as_view(), name="alpr-scan"),
]
