# finanzas_facturacion/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status, viewsets
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.db import transaction
from decimal import Decimal
import stripe
import logging

from .models import Pago
from operaciones_inventario.modelsOrdenTrabajo import OrdenTrabajo
from .serializers.serializersPagos import PagoSerializer, PagoCreateSerializer
from personal_admin.views import registrar_bitacora
from personal_admin.models import Bitacora

# Configurar logging
logger = logging.getLogger(__name__)

# Configurar Stripe con la clave secreta
stripe.api_key = settings.STRIPE_SECRET_KEY


# ============================================
# VISTAS SIMPLES DE STRIPE (PARA PROYECTO UNIVERSITARIO)
# ============================================

class CreatePaymentIntentOrden(APIView):
    """
    POST { "orden_trabajo_id": 123, "monto": 500.00, "descripcion": "..." }
    -> Crea un PaymentIntent y devuelve { client_secret }
    Usar con Stripe Elements en el frontend (sin redirección).
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        orden_trabajo_id = request.data.get("orden_trabajo_id")
        monto = request.data.get("monto")
        descripcion = request.data.get("descripcion", "")
        
        if not orden_trabajo_id:
            return Response(
                {"error": "orden_trabajo_id es requerido"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener la orden de trabajo
        orden = get_object_or_404(OrdenTrabajo, id=orden_trabajo_id)
        
        # Usar el monto proporcionado o el total de la orden
        if not monto:
            monto = orden.total if hasattr(orden, 'total') and orden.total else Decimal('0')
        
        monto = Decimal(str(monto))
        
        if monto <= 0:
            return Response(
                {"error": "El monto debe ser mayor a 0"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Convertir a centavos
        amount_cents = int(monto * 100)
        
        # Idempotencia: agregar timestamp para permitir múltiples intentos
        import time
        idem_key = f"pi-orden-{orden.id}-{int(time.time())}"
        
        logger.info(f"📤 Creando Payment Intent para orden #{orden.id}, monto: Bs.{monto}")
        
        try:
            # Crear Payment Intent en Stripe
            pi = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency="bob",  # Bolivianos (en producción usa "usd" si necesitas)
                metadata={"orden_trabajo_id": str(orden.id)},
                automatic_payment_methods={"enabled": True},
                idempotency_key=idem_key,
                description=descripcion or f"Pago Orden #{orden.id}"
            )
            
            # Guardar el Payment Intent ID en un nuevo registro de Pago
            pago = Pago.objects.create(
                orden_trabajo=orden,
                monto=monto,
                metodo_pago='stripe',
                estado='procesando',
                stripe_payment_intent_id=pi.id,
                currency='bob',
                descripcion=descripcion or f"Pago de orden de trabajo #{orden.id}",
                usuario=request.user if request.user.is_authenticated else None
            )
            
            logger.info(f"✅ Payment Intent {pi.id} creado. Pago ID: {pago.id}")
            
            return Response({
                "client_secret": pi.client_secret,
                "payment_intent_id": pi.id,
                "pago_id": pago.id,
                "monto": float(monto)
            }, status=status.HTTP_201_CREATED)
            
        except Exception as stripe_error:
            # Capturar cualquier error de Stripe
            error_message = str(stripe_error)
            if 'stripe' in error_message.lower():
                logger.error(f"❌ Error de Stripe: {error_message}")
                return Response(
                    {"error": f"Error con Stripe: {error_message}"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Cualquier otro error
            logger.error(f"❌ Error inesperado: {error_message}")
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                {"error": f"Error interno: {error_message}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VerifyPaymentIntentOrden(APIView):
    """
    POST { "payment_intent_id": "pi_xxx" }
    -> Devuelve estado del PaymentIntent y marca el pago como completado si 'succeeded'
    (útil para verificar desde el front sin webhooks).
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        pi_id = request.data.get("payment_intent_id")
        
        if not pi_id:
            return Response(
                {"error": "payment_intent_id requerido"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            logger.info(f"🔍 Verificando Payment Intent: {pi_id}")
            
            # Recuperar Payment Intent de Stripe
            pi = stripe.PaymentIntent.retrieve(pi_id)
            status_pi = pi.get("status")  # 'succeeded', 'requires_payment_method', etc.
            orden_trabajo_id = (pi.get("metadata") or {}).get("orden_trabajo_id")
            
            logger.info(f"📊 Estado del Payment Intent: {status_pi}")
            
            # Buscar el pago por Payment Intent ID
            pago = Pago.objects.filter(stripe_payment_intent_id=pi_id).first()
            
            if not pago:
                logger.error(f"❌ No se encontró el pago con Payment Intent: {pi_id}")
                return Response({
                    "error": "Pago no encontrado en la base de datos",
                    "payment_intent_id": pi_id
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Si el pago fue exitoso en Stripe, actualizar el registro
            if status_pi == "succeeded":
                pago.estado = 'completado'
                pago.save(update_fields=['estado'])
                
                logger.info(f"✅ Pago #{pago.id} confirmado exitosamente")
                
                # Serializar el pago para devolver datos completos
                pago_data = PagoSerializer(pago).data
                
                return Response({
                    "status": status_pi,
                    "orden_trabajo_id": orden_trabajo_id,
                    "pago": pago_data,
                    "message": "Pago confirmado exitosamente"
                }, status=status.HTTP_200_OK)
            
            # Si el pago no fue exitoso
            return Response({
                "status": status_pi,
                "orden_trabajo_id": orden_trabajo_id,
                "pago": PagoSerializer(pago).data,
                "message": f"Pago en estado: {status_pi}"
            }, status=status.HTTP_200_OK)
            
        except Pago.DoesNotExist:
            logger.error(f"❌ Pago con Payment Intent {pi_id} no encontrado en DB")
            return Response(
                {"error": "Pago no encontrado en la base de datos"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            # Capturar cualquier error (incluidos los de Stripe)
            error_message = str(e)
            logger.error(f"❌ Error: {error_message}")
            import traceback
            logger.error(traceback.format_exc())
            
            return Response(
                {"error": f"Error al procesar: {error_message}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================
# VIEWSET PARA PAGOS MANUALES (CRUD BÁSICO)
# ============================================

class PagoViewSet(viewsets.ModelViewSet):
    """
    ViewSet simple para gestionar pagos manuales (efectivo, transferencia, etc.)
    """
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PagoSerializer
    
    def get_queryset(self):
        """Retorna pagos filtrados por orden de trabajo"""
        queryset = Pago.objects.all().select_related('orden_trabajo', 'usuario').order_by('-fecha_pago')
        
        # Filtro por orden de trabajo
        orden_id = self.request.query_params.get('orden_trabajo', None)
        if orden_id:
            queryset = queryset.filter(orden_trabajo_id=orden_id)
        
        # Filtro por estado
        estado = self.request.query_params.get('estado', None)
        if estado:
            queryset = queryset.filter(estado=estado)
        
        # Filtro por método de pago
        metodo = self.request.query_params.get('metodo_pago', None)
        if metodo:
            queryset = queryset.filter(metodo_pago=metodo)
        
        return queryset.order_by('-fecha_pago')
    
    def get_serializer_class(self):
        """Retorna el serializer según la acción"""
        if self.action == 'create':
            return PagoCreateSerializer
        return PagoSerializer
    
    def perform_create(self, serializer):
        """Crear pago manual (efectivo, transferencia, etc.)"""
        pago = serializer.save(
            estado='completado',
            usuario=self.request.user
        )
        logger.info(f"✅ Pago manual #{pago.id} creado: {pago.metodo_pago} por Bs.{pago.monto}")
