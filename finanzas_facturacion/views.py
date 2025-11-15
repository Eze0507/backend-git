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
from rest_framework.permissions import IsAuthenticated

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
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        user_tenant = user.profile.tenant
        orden_trabajo_id = request.data.get("orden_trabajo_id")
        monto = request.data.get("monto")
        descripcion = request.data.get("descripcion", "")
        orden = get_object_or_404(OrdenTrabajo, id=orden_trabajo_id, tenant=user_tenant)
        
        
        # Obtener la orden de trabajo
        
        
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
            # Configurado para NO permitir métodos de pago con redirección (más simple para móvil)
            pi = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency="bob",  # Bolivianos (en producción usa "usd" si necesitas)
                metadata={"orden_trabajo_id": str(orden.id), "tenant_id": user_tenant.id},
                automatic_payment_methods={
                    "enabled": True,
                    "allow_redirects": "never"  # Evitar métodos que requieren return_url
                },
                idempotency_key=idem_key,
                description=descripcion or f"Pago Orden #{orden.id}"
            )
            
            # Guardar el Payment Intent ID en un nuevo registro de Pago
            pago, created = Pago.objects.get_or_create(
                stripe_payment_intent_id=pi.id,
                tenant=user_tenant,
                defaults={  # <-- Estos campos solo se usan si se CREA uno nuevo
                    'orden_trabajo': orden,
                    'monto': monto,
                    'metodo_pago': 'stripe',
                    'estado': 'procesando',
                    'currency': 'bob',
                    'descripcion': descripcion or f"Pago de orden de trabajo #{orden.id}",
                    'usuario': request.user
                }
            )
            
            if created:
                logger.info(f"✅ Payment Intent {pi.id} y Pago ID: {pago.id} creados.")
            else:
                logger.info(f"🔁 Pago ID: {pago.id} (existente) recuperado para Payment Intent {pi.id}.")
            
            return Response({
                "client_secret": pi.client_secret,
                "payment_intent_id": pi.id,
                "pago_id": pago.id,
                "monto": float(monto)
            }, status=status.HTTP_201_CREATED)
            
        except stripe.StripeError as stripe_error:
            # Capturar cualquier error de Stripe
            error_message = str(stripe_error)
            logger.error(f"❌ Error de Stripe: {error_message}")
            return Response(
                {"error": f"Error con Stripe: {error_message}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            # Cualquier otro error
            error_message = str(e)
            logger.error(f"❌ Error inesperado: {error_message}")
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                {"error": f"Error interno: {error_message}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ConfirmPaymentAutoOrden(APIView):
    """
    POST { "payment_intent_id": "pi_xxx" }
    -> Confirma el Payment Intent automáticamente usando Payment Method de prueba
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        pi_id = request.data.get("payment_intent_id")
        
        if not pi_id:
            return Response(
                {"error": "payment_intent_id requerido"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user
        user_tenant = user.profile.tenant
        
        try:
            pago = get_object_or_404(Pago, stripe_payment_intent_id=pi_id, tenant=user_tenant)
            logger.info(f"🔄 Confirmando Payment Intent automáticamente: {pi_id} para Tenant : {user_tenant.id}")
            
            # Usar el Payment Method de prueba predefinido de Stripe
            # pm_card_visa es un payment method de prueba que siempre funciona
            TEST_PAYMENT_METHOD = "pm_card_visa"
            
            logger.info(f"💳 Usando Payment Method de prueba: {TEST_PAYMENT_METHOD}")
            
            # Confirmar el Payment Intent con el payment method de prueba
            pi = stripe.PaymentIntent.confirm(
                pi_id,
                payment_method=TEST_PAYMENT_METHOD,
            )
            
            status_pi = pi.get("status")
            logger.info(f"✅ Payment Intent confirmado: {status_pi}")
            
            return Response({
                "success": True,
                "status": status_pi,
                "payment_intent_id": pi_id,
                "message": "Pago confirmado automáticamente con tarjeta de prueba"
            }, status=status.HTTP_200_OK)
            
        except stripe.StripeError as e:
            error_message = str(e)
            logger.error(f"❌ Error de Stripe al confirmar pago: {error_message}")
            return Response(
                {"error": f"Error de Stripe: {error_message}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"❌ Error al confirmar pago: {error_message}")
            import traceback
            logger.error(traceback.format_exc())
            
            return Response(
                {"error": f"Error al confirmar pago: {error_message}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ConfirmPaymentWithCardOrden(APIView):
    """
    POST { 
        "payment_intent_id": "pi_xxx",
        "card_number": "4242424242424242",  # Opcional si usas payment_method_id
        "exp_month": "04",                   # Opcional si usas payment_method_id
        "exp_year": "26",                    # Opcional si usas payment_method_id
        "cvc": "123",                        # Opcional si usas payment_method_id
        "payment_method_id": "pm_card_visa"  # Opcional: usar payment method existente
    }
    -> Confirma el Payment Intent con payment method existente o crea uno nuevo
    
    IMPORTANTE: Stripe v13+ requiere usar payment_method_id de prueba en lugar de
    números de tarjeta crudos. Para producción, usa Stripe Elements en el frontend.
    Payment Methods de prueba: pm_card_visa, pm_card_mastercard, pm_card_amex, etc.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        pi_id = request.data.get("payment_intent_id")
        payment_method_id = request.data.get("payment_method_id")
        card_number = request.data.get("card_number", "").replace(" ", "")
        exp_month = request.data.get("exp_month")
        exp_year = request.data.get("exp_year")
        cvc = request.data.get("cvc")
        
        # Validaciones
        if not pi_id:
            return Response(
                {"error": "payment_intent_id requerido"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user
        user_tenant = user.profile.tenant
        
        try:
            pago = get_object_or_404(
                Pago, 
                stripe_payment_intent_id=pi_id, 
                tenant=user_tenant
            )
        except Exception as e:
            logger.warn(f"Intento de confirmación de pago fallido. PI: {pi_id}, User: {user.id}. No se encontró el pago o no pertenece al tenant.")
            return Response(
                {"error": "Payment Intent no encontrado o no autorizado."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Si no se proporciona payment_method_id, intentar crear uno
        if not payment_method_id:
            # Mapear números de tarjeta de prueba a payment methods de prueba
            test_cards = {
                "4242424242424242": "pm_card_visa",
                "5555555555554444": "pm_card_mastercard",
                "378282246310005": "pm_card_amex",
            }
            
            if card_number in test_cards:
                # Usar payment method de prueba predefinido
                payment_method_id = test_cards[card_number]
                logger.info(f"💳 Usando payment method de prueba: {payment_method_id}")
            else:
                return Response(
                    {
                        "error": "Para pruebas, usa payment_method_id (ej: 'pm_card_visa') o tarjeta de prueba 4242424242424242",
                        "test_cards": list(test_cards.keys()),
                        "test_payment_methods": list(test_cards.values())
                    }, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        try:
            logger.info(f"🔄 Procesando pago para Payment Intent: {pi_id}")
            logger.info(f"💳 Payment Method: {payment_method_id}")
            
            # Confirmar el Payment Intent con el payment method
            pi = stripe.PaymentIntent.confirm(
                pi_id,
                payment_method=payment_method_id,
            )
            
            status_pi = pi.get("status")
            logger.info(f"✅ Payment Intent confirmado: {status_pi}")
            
            # Si el pago fue exitoso, actualizar el registro
            if status_pi == "succeeded":
                pago.estado = 'completado'
                pago.save(update_fields=['estado'])
                if pago.orden_trabajo:
                    # Doble chequeo por si acaso (aunque 'pago' ya es seguro)
                    if pago.orden_trabajo.tenant == user_tenant:
                        pago.orden_trabajo.pago = True
                        pago.orden_trabajo.save(update_fields=['pago'])
                        logger.info(f"✅ Orden #{pago.orden_trabajo.id} marcada como pagada")
                    else:
                        # Esto no debería pasar si tu lógica de creación de Pago es correcta
                        logger.error(f"¡ALERTA DE SEGURIDAD! Pago {pago.id} y Orden {pago.orden_trabajo.id} tienen tenants diferentes.")
                
                logger.info(f"✅ Pago #{pago.id} marcado como completado")
            
            return Response({
                "success": True,
                "status": status_pi,
                "payment_intent_id": pi_id,
                "payment_method_id": payment_method_id,
                "message": "Pago procesado exitosamente"
            }, status=status.HTTP_200_OK)
            
        except stripe.StripeError as e:
            # Error de Stripe (incluye CardError, InvalidRequestError, etc.)
            error_message = getattr(e, 'user_message', None) or str(e)
            logger.error(f"❌ Error de Stripe: {error_message}")
            
            return Response(
                {"error": f"Error de Stripe: {error_message}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            error_message = str(e)
            logger.error(f"❌ Error al procesar pago: {error_message}")
            import traceback
            logger.error(traceback.format_exc())
            
            return Response(
                {"error": f"Error al procesar pago: {error_message}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VerifyPaymentIntentOrden(APIView):
    """
    POST { "payment_intent_id": "pi_xxx" }
    -> Devuelve estado del PaymentIntent y marca el pago como completado si 'succeeded'
    (útil para verificar desde el front sin webhooks).
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        pi_id = request.data.get("payment_intent_id")
        
        if not pi_id:
            return Response(
                {"error": "payment_intent_id requerido"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user
        user_tenant = user.profile.tenant
        
        try:
            logger.info(f"🔍 Verificando Payment Intent: {pi_id}")
            
            pago = get_object_or_404(
                Pago, 
                stripe_payment_intent_id=pi_id, 
                tenant=user_tenant
            )
            
            # Recuperar Payment Intent de Stripe
            pi = stripe.PaymentIntent.retrieve(pi_id)
            status_pi = pi.get("status")  # 'succeeded', 'requires_payment_method', etc.
            orden_trabajo_id = (pi.get("metadata") or {}).get("orden_trabajo_id")
            
            logger.info(f"📊 Estado del Payment Intent: {status_pi}")
            
            # Si el pago fue exitoso en Stripe, actualizar el registro
            if status_pi == "succeeded":
                pago.estado = 'completado'
                pago.save(update_fields=['estado'])
                
                # Actualizar estado de pago de la orden
                if pago.orden_trabajo:
                    pago.orden_trabajo.pago = True
                    pago.orden_trabajo.save(update_fields=['pago'])
                    logger.info(f"✅ Orden #{pago.orden_trabajo.id} marcada como pagada")
                
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
        except stripe.StripeError as e:
            error_message = str(e)
            logger.error(f"❌ Error de Stripe: {error_message}")
            return Response(
                {"error": f"Error de Stripe: {error_message}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            # Capturar cualquier otro error
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
        """Retorna pagos filtrados según el rol del usuario"""
        user = self.request.user
        
        user_tenant = user.profile.tenant
        
        # Queryset base con relaciones
        queryset = Pago.objects.filter(
            tenant=user_tenant
        ).select_related('orden_trabajo', 'orden_trabajo__cliente', 'usuario')
        
        # Verificar si es administrador
        is_admin = user.groups.filter(name='administrador').exists()
        
        if not is_admin:
            # Si es cliente, solo mostrar pagos de sus propias órdenes
            # Buscar cliente asociado al usuario
            from clientes_servicios.models import Cliente
            try:
                cliente = Cliente.objects.get(usuario=user, tenant=user_tenant)
                queryset = queryset.filter(orden_trabajo__cliente=cliente)
                logger.info(f"🔍 Cliente {cliente.nombre} (Tenant {user_tenant.id}) consultando sus pagos")
            except Cliente.DoesNotExist:
                # Si no es cliente ni admin, no mostrar pagos
                queryset = queryset.none()
                logger.warning(f"⚠️ Usuario {user.username} (Tenant {user_tenant.id}) sin cliente asociado intentó acceder a pagos")
        
        # Filtros adicionales por query params
        orden_id = self.request.query_params.get('orden_trabajo', None)
        if orden_id:
            queryset = queryset.filter(orden_trabajo_id=orden_id)
        
        orden_param = self.request.query_params.get('orden', None)
        if orden_param:
            queryset = queryset.filter(orden_trabajo_id=orden_param)
        
        estado = self.request.query_params.get('estado', None)
        if estado:
            queryset = queryset.filter(estado=estado)
        
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
        user_tenant = self.request.user.profile.tenant
        pago = serializer.save(
            tenant=user_tenant,
            estado='completado',
            usuario=self.request.user
        )
        
        # Actualizar estado de pago de la orden
        if pago.orden_trabajo:
            pago.orden_trabajo.pago = True
            pago.orden_trabajo.save(update_fields=['pago'])
            logger.info(f"✅ Orden #{pago.orden_trabajo.id} marcada como pagada")
        
        # Registrar en bitácora
        try:
            registrar_bitacora(
                usuario=self.request.user,
                accion=Bitacora.Accion.CREAR,
                modulo=Bitacora.Modulo.FINANZAS,
                descripcion=f"Pago manual registrado: {pago.metodo_pago} por Bs.{pago.monto} para orden #{pago.orden_trabajo.id if pago.orden_trabajo else 'N/A'}",
                request=self.request
            )
        except Exception as e:
            logger.warning(f"⚠️ No se pudo registrar en bitácora: {e}")
        
        logger.info(f"✅ Pago manual #{pago.id} (Tenant {user_tenant.id}) creado: {pago.metodo_pago} por Bs.{pago.monto}")
