# servicios_IA/urls.py
from django.urls import path
from .views import AlprScanView
from .views_chatbot import GeminiChatView


urlpatterns = [
    path("alpr/", AlprScanView.as_view(), name="alpr-scan"),
    path("chatbot/", GeminiChatView.as_view(), name="chatbot"),
]
