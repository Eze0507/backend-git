from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models_device_token import DeviceToken
from .serializers_device_token import DeviceTokenSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_device_token(request):
    """
    Registra o actualiza el token FCM del dispositivo del usuario
    
    POST /api/device-token/register/
    Body: {
        "token": "FCM_TOKEN_STRING",
        "platform": "android"  // o "ios"
    }
    """
    token = request.data.get('token')
    platform = request.data.get('platform', 'android')
    
    if not token:
        return Response({
            'message': 'Token es requerido',
            'errors': {'token': ['Este campo es requerido']}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Buscar si el token ya existe
    device_token = DeviceToken.objects.filter(token=token).first()
    
    if device_token:
        # Token existe, actualizar datos
        device_token.user = request.user
        device_token.platform = platform
        device_token.is_active = True
        device_token.save()
    else:
        # Token no existe, crear uno nuevo
        device_token = DeviceToken.objects.create(
            user=request.user,
            token=token,
            platform=platform,
            is_active=True
        )
    
    return Response({
        'message': 'Token registrado exitosamente',
        'data': DeviceTokenSerializer(device_token).data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unregister_device_token(request):
    """
    Desactiva un token FCM (cuando el usuario cierra sesión)
    
    POST /api/device-token/unregister/
    Body: {
        "token": "FCM_TOKEN_STRING"
    }
    """
    token = request.data.get('token')
    
    if not token:
        return Response({
            'message': 'Token es requerido'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        device_token = DeviceToken.objects.get(token=token, user=request.user)
        device_token.is_active = False
        device_token.save()
        
        return Response({
            'message': 'Token desactivado exitosamente'
        }, status=status.HTTP_200_OK)
    
    except DeviceToken.DoesNotExist:
        return Response({
            'message': 'Token no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
