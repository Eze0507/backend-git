"""
Serializers para la aplicación servicios_IA
"""
from rest_framework import serializers
from .serializersPlaca import LecturaPlacaSerializer, AlprScanSerializer

__all__ = ['LecturaPlacaSerializer', 'AlprScanSerializer']
