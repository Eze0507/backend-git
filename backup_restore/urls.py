"""
URLs para el módulo de Backup y Restore
"""
from django.urls import path
from .views import BackupView, RestoreView

app_name = 'backup_restore'

urlpatterns = [
    path('backup/', BackupView.as_view(), name='backup'),
    path('restore/', RestoreView.as_view(), name='restore'),
]

