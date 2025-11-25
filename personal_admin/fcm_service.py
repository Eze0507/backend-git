"""
Servicio para enviar notificaciones push mediante Firebase Cloud Messaging (FCM)
"""
import json
import logging
import requests
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from django.conf import settings

logger = logging.getLogger(__name__)


class FCMService:
    """Servicio para enviar notificaciones push a través de FCM"""
    
    SCOPES = ['https://www.googleapis.com/auth/firebase.messaging']
    
    def __init__(self):
        self.project_id = getattr(settings, 'FIREBASE_PROJECT_ID', None)
        self.service_account_json = getattr(settings, 'FIREBASE_SERVICE_ACCOUNT_JSON', None)
        
        if not self.project_id or not self.service_account_json:
            logger.warning("Firebase credentials not configured in settings")
            self.credentials = None
        else:
            try:
                service_account_info = json.loads(self.service_account_json)
                self.credentials = service_account.Credentials.from_service_account_info(
                    service_account_info,
                    scopes=self.SCOPES
                )
            except Exception as e:
                logger.error(f"Error loading Firebase credentials: {e}")
                self.credentials = None
    
    def _get_access_token(self):
        """Obtiene el access token de Google para FCM"""
        if not self.credentials:
            raise ValueError("Firebase credentials not configured")
        
        if not self.credentials.valid:
            self.credentials.refresh(Request())
        
        return self.credentials.token
    
    def send_to_token(self, token, title, body, data=None):
        """
        Envía notificación a un token FCM específico
        
        Args:
            token (str): Token FCM del dispositivo
            title (str): Título de la notificación
            body (str): Mensaje de la notificación
            data (dict): Datos adicionales opcionales
        
        Returns:
            dict: {'success': bool, 'message_id': str} o {'success': False, 'error': str}
        """
        if not self.credentials:
            return {'success': False, 'error': 'Firebase not configured'}
        
        try:
            access_token = self._get_access_token()
            url = f'https://fcm.googleapis.com/v1/projects/{self.project_id}/messages:send'
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json; UTF-8',
            }
            
            message = {
                'message': {
                    'token': token,
                    'notification': {
                        'title': title,
                        'body': body,
                    },
                }
            }
            
            if data:
                message['message']['data'] = {k: str(v) for k, v in data.items()}
            
            response = requests.post(url, headers=headers, json=message, timeout=10)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'message_id': response.json().get('name')
                }
            else:
                logger.error(f"FCM Error: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': response.text
                }
        
        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_to_user(self, user, title, body, data=None):
        """
        Envía notificación a todos los dispositivos activos de un usuario
        
        Args:
            user: Instancia del modelo User
            title (str): Título de la notificación
            body (str): Mensaje de la notificación
            data (dict): Datos adicionales opcionales
        
        Returns:
            dict: Resumen con total enviado, exitosos y fallidos
        """
        from .models_device_token import DeviceToken
        
        tokens = DeviceToken.objects.filter(user=user, is_active=True)
        
        if not tokens.exists():
            return {
                'success': False,
                'message': 'No active tokens found',
                'total': 0,
                'successful': 0,
                'failed': 0
            }
        
        results = {
            'total': tokens.count(),
            'successful': 0,
            'failed': 0
        }
        
        for device_token in tokens:
            result = self.send_to_token(device_token.token, title, body, data)
            
            if result['success']:
                results['successful'] += 1
            else:
                results['failed'] += 1
                
                # Marcar token como inactivo si es inválido
                error = str(result.get('error', '')).upper()
                if 'NOT_FOUND' in error or 'UNREGISTERED' in error or 'INVALID' in error:
                    device_token.is_active = False
                    device_token.save()
        
        results['success'] = results['successful'] > 0
        return results


# Instancia global del servicio
fcm_service = FCMService()


# Funciones helper simplificadas
def send_notification(user, title, body, data=None):
    """
    Envía notificación push a un usuario
    
    Uso:
        from personal_admin.fcm_service import send_notification
        send_notification(user, "Nuevo mensaje", "Tienes una orden de trabajo asignada")
    """
    return fcm_service.send_to_user(user, title, body, data)


def send_notification_to_token(token, title, body, data=None):
    """
    Envía notificación a un token específico
    
    Uso:
        from personal_admin.fcm_service import send_notification_to_token
        send_notification_to_token(token, "Título", "Mensaje")
    """
    return fcm_service.send_to_token(token, title, body, data)
