import stripe
import logging
from decimal import Decimal
from django.conf import settings
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .modelsPagos import Pago
from operaciones_inventario.modelsOrdenTrabajo import OrdenTrabajo
from .serializers.serializersPagos import (
    PagoSerializer,
    PagoCreateSerializer,
    StripePaymentIntentSerializer,
    StripeConfirmPaymentSerializer,
    StripeRefundSerializer
)
from personal_admin.views import registrar_bitacora
from personal_admin.models import Bitacora

# Configurar logging
logger = logging.getLogger(__name__)

# Configurar Stripe con la clave secreta
stripe.api_key = settings.STRIPE_SECRET_KEY


class PagoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar los pagos de órdenes de trabajo.
    Incluye integración completa con Stripe.
    """
    
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Retorna el serializer según la acción"""
        if self.action == 'create':
            return PagoCreateSerializer
        return PagoSerializer
    
    def get_queryset(self):
        """
        Retorna los pagos filtrados por orden de trabajo si se proporciona.
        También soporta filtro por estado y método de pago.
        """
        queryset = Pago.objects.all().select_related('orden_trabajo', 'orden_trabajo__cliente', 'usuario')
        
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
    
    def perform_create(self, serializer):
        """
        Crear un pago manual (efectivo, transferencia, tarjeta física, etc.)
        Automáticamente marca el pago como completado.
        """
        with transaction.atomic():
            pago = serializer.save(
                estado='completado',
                usuario=self.request.user
            )
            
            # Registrar en bitácora
            registrar_bitacora(
                usuario=self.request.user,
                accion=Bitacora.Accion.CREAR,
                modulo=Bitacora.Modulo.ORDEN_TRABAJO,
                descripcion=f"Pago manual registrado: {pago.metodo_pago} por Bs. {pago.monto:.2f} para orden #{pago.orden_trabajo.id}",
                request=self.request
            )
            
            logger.info(f"Pago manual #{pago.id} creado por usuario {self.request.user.username}")
    
    @action(detail=False, methods=['post'], url_path='create-payment-intent')
    def create_payment_intent(self, request):
        """
        Endpoint: POST /api/pagos/create-payment-intent/
        
        Crea un Payment Intent en Stripe para procesar un pago con tarjeta.
        
        Body:
        {
            "orden_trabajo_id": 123,
            "monto": 500.00,  // Opcional, usa el total de la orden si no se proporciona
            "descripcion": "Pago de reparación de motor"  // Opcional
        }
        
        Respuesta exitosa:
        {
            "clientSecret": "pi_xxx_secret_xxx",
            "paymentIntentId": "pi_xxxxxxxxxxxxx",
            "pago_id": 456,
            "monto": 500.00
        }
        """
        serializer = StripePaymentIntentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        orden_id = serializer.validated_data['orden_trabajo_id']
        descripcion = serializer.validated_data.get('descripcion', '')
        
        try:
            orden = OrdenTrabajo.objects.get(id=orden_id)
            
            # Usar el monto proporcionado o el total de la orden
            monto = serializer.validated_data.get('monto')
            if monto is None:
                monto = orden.total if orden.total else Decimal('0.00')
            
            # Validar que el monto sea mayor a 0
            if float(monto) <= 0:
                return Response(
                    {'error': 'El monto debe ser mayor a 0. La orden no tiene monto asignado o es cero.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Convertir a centavos (Stripe trabaja en centavos/céntimos)
            monto_centavos = int(float(monto) * 100)
            
            logger.info(f"Creando Payment Intent para orden #{orden.id} por Bs. {monto}")
            
            # Obtener nombre del cliente de forma segura
            cliente_nombre = 'Sin cliente'
            if hasattr(orden, 'cliente') and orden.cliente:
                if hasattr(orden.cliente, 'nombre') and hasattr(orden.cliente, 'apellido'):
                    cliente_nombre = f"{orden.cliente.nombre} {orden.cliente.apellido}"
                elif hasattr(orden.cliente, 'nombre'):
                    cliente_nombre = orden.cliente.nombre
            
            # Crear Payment Intent en Stripe
            payment_intent = stripe.PaymentIntent.create(
                amount=monto_centavos,
                currency='bob',  # Bolivianos - cambiar según tu país (usd, eur, etc.)
                description=descripcion or f"Pago de orden de trabajo #{orden.id}",
                metadata={
                    'orden_trabajo_id': orden.id,
                    'numero_orden': getattr(orden, 'numero_orden', f'OT-{orden.id}'),
                    'cliente_nombre': cliente_nombre,
                    'usuario_id': request.user.id,
                    'usuario_nombre': request.user.username,
                },
                automatic_payment_methods={
                    'enabled': True,
                },
            )
            
            # Crear registro de pago en la base de datos
            with transaction.atomic():
                pago = Pago.objects.create(
                    orden_trabajo=orden,
                    monto=monto,
                    metodo_pago='stripe',
                    estado='procesando',
                    stripe_payment_intent_id=payment_intent.id,
                    descripcion=descripcion,
                    usuario=request.user
                )
                
                # Registrar en bitácora
                registrar_bitacora(
                    usuario=request.user,
                    accion=Bitacora.Accion.CREAR,
                    modulo=Bitacora.Modulo.ORDEN_TRABAJO,
                    descripcion=f"Payment Intent de Stripe creado por Bs. {monto:.2f} para orden #{orden.id}",
                    request=request
                )
            
            logger.info(f"Payment Intent {payment_intent.id} creado exitosamente. Pago ID: {pago.id}")
            
            return Response({
                'client_secret': payment_intent.client_secret,
                'payment_intent_id': payment_intent.id,
                'pago_id': pago.id,
                'monto': float(monto),
                'message': 'Payment Intent creado exitosamente'
            }, status=status.HTTP_201_CREATED)
            
        except OrdenTrabajo.DoesNotExist:
            logger.error(f"Orden de trabajo #{orden_id} no encontrada")
            return Response(
                {'error': 'Orden de trabajo no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        except stripe.error.StripeError as e:
            logger.error(f"Error de Stripe: {str(e)}")
            return Response(
                {'error': f'Error de Stripe: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error inesperado: {str(e)}")
            return Response(
                {'error': f'Error inesperado: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], url_path='confirm-payment')
    def confirm_payment(self, request):
        """
        Endpoint: POST /api/pagos/confirm-payment/
        
        Confirma que un pago de Stripe fue exitoso y actualiza el estado.
        
        Body:
        {
            "payment_intent_id": "pi_xxxxxxxxxxxxx"
        }
        
        Respuesta exitosa:
        {
            "message": "Pago confirmado exitosamente",
            "pago": { ... datos del pago ... }
        }
        """
        serializer = StripeConfirmPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        payment_intent_id = serializer.validated_data['payment_intent_id']
        
        try:
            logger.info(f"Confirmando Payment Intent: {payment_intent_id}")
            
            # Obtener el Payment Intent de Stripe
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            logger.info(f"Payment Intent obtenido. Status: {payment_intent.status}")
            
            # Buscar el pago en la base de datos
            pago = Pago.objects.get(stripe_payment_intent_id=payment_intent_id)
            logger.info(f"Pago encontrado en DB. ID: {pago.id}, Estado actual: {pago.estado}")
            
            with transaction.atomic():
                if payment_intent.status == 'succeeded':
                    pago.estado = 'completado'
                    
                    # Obtener charge_id de forma segura
                    try:
                        if hasattr(payment_intent, 'charges') and payment_intent.charges and hasattr(payment_intent.charges, 'data'):
                            if len(payment_intent.charges.data) > 0:
                                pago.stripe_charge_id = payment_intent.charges.data[0].id
                    except Exception as e:
                        logger.warning(f"No se pudo obtener charge_id: {str(e)}")
                    
                    # Si existe customer en Stripe, guardarlo
                    if hasattr(payment_intent, 'customer') and payment_intent.customer:
                        pago.stripe_customer_id = payment_intent.customer
                    
                    pago.save()
                    
                    # Registrar en bitácora
                    registrar_bitacora(
                        usuario=request.user,
                        accion=Bitacora.Accion.EDITAR,
                        modulo=Bitacora.Modulo.ORDEN_TRABAJO,
                        descripcion=f"Pago completado exitosamente: Stripe por Bs. {pago.monto:.2f} para orden #{pago.orden_trabajo.id}",
                        request=request
                    )
                    
                    logger.info(f"Pago #{pago.id} confirmado exitosamente")
                    
                    return Response({
                        'message': 'Pago confirmado exitosamente',
                        'pago': PagoSerializer(pago).data
                    }, status=status.HTTP_200_OK)
                    
                elif payment_intent.status == 'canceled':
                    pago.estado = 'cancelado'
                    pago.save()
                    
                    logger.warning(f"Payment Intent {payment_intent_id} fue cancelado")
                    
                    return Response({
                        'message': 'El pago fue cancelado',
                        'status': payment_intent.status
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
                else:
                    pago.estado = 'fallido'
                    pago.save()
                    
                    logger.error(f"Payment Intent {payment_intent_id} falló con estado: {payment_intent.status}")
                    
                    return Response({
                        'error': 'El pago no se completó',
                        'status': payment_intent.status
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
        except Pago.DoesNotExist:
            logger.error(f"Pago con Payment Intent {payment_intent_id} no encontrado")
            return Response(
                {'error': 'Pago no encontrado en la base de datos'},
                status=status.HTTP_404_NOT_FOUND
            )
        except stripe.error.StripeError as e:
            logger.error(f"Error de Stripe al confirmar pago: {str(e)}")
            return Response(
                {'error': f'Error de Stripe: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error inesperado al confirmar pago: {str(e)}")
            return Response(
                {'error': f'Error inesperado: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], url_path='refund')
    def refund_payment(self, request):
        """
        Endpoint: POST /api/pagos/refund/
        
        Reembolsa un pago procesado con Stripe.
        
        Body:
        {
            "pago_id": 456,
            "monto": 100.00,  // Opcional, reembolsa el total si no se proporciona
            "razon": "Cliente insatisfecho"  // Opcional
        }
        
        Respuesta exitosa:
        {
            "message": "Reembolso procesado exitosamente",
            "refund_id": "re_xxxxxxxxxxxxx",
            "monto_reembolsado": 100.00
        }
        """
        serializer = StripeRefundSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        pago_id = serializer.validated_data['pago_id']
        monto_reembolso = serializer.validated_data.get('monto')
        razon = serializer.validated_data.get('razon', 'Reembolso solicitado por el cliente')
        
        try:
            pago = Pago.objects.get(id=pago_id)
            
            if not pago.puede_reembolsar():
                return Response(
                    {'error': 'Este pago no puede ser reembolsado'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Usar el monto total si no se especifica uno parcial
            if monto_reembolso is None:
                monto_reembolso = pago.monto
            
            # Convertir a centavos
            monto_reembolso_centavos = int(float(monto_reembolso) * 100)
            
            logger.info(f"Procesando reembolso de Bs. {monto_reembolso} para pago #{pago.id}")
            
            # Crear reembolso en Stripe
            refund = stripe.Refund.create(
                payment_intent=pago.stripe_payment_intent_id,
                amount=monto_reembolso_centavos,
                reason='requested_by_customer',
                metadata={
                    'razon': razon,
                    'usuario_id': request.user.id,
                    'usuario_nombre': request.user.username,
                }
            )
            
            with transaction.atomic():
                # Actualizar estado del pago
                pago.estado = 'reembolsado'
                pago.descripcion = f"{pago.descripcion or ''}\nReembolso: {razon}".strip()
                pago.save()
                
                # Registrar en bitácora
                registrar_bitacora(
                    usuario=request.user,
                    accion=Bitacora.Accion.EDITAR,
                    modulo=Bitacora.Modulo.ORDEN_TRABAJO,
                    descripcion=f"Reembolso de Bs. {monto_reembolso:.2f} procesado para pago #{pago.id} de orden #{pago.orden_trabajo.id}",
                    request=request
                )
            
            logger.info(f"Reembolso {refund.id} procesado exitosamente para pago #{pago.id}")
            
            return Response({
                'message': 'Reembolso procesado exitosamente',
                'refund_id': refund.id,
                'monto_reembolsado': float(monto_reembolso),
                'pago': PagoSerializer(pago).data
            }, status=status.HTTP_200_OK)
            
        except Pago.DoesNotExist:
            logger.error(f"Pago #{pago_id} no encontrado")
            return Response(
                {'error': 'Pago no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        except stripe.error.StripeError as e:
            logger.error(f"Error de Stripe al procesar reembolso: {str(e)}")
            return Response(
                {'error': f'Error de Stripe: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error inesperado al procesar reembolso: {str(e)}")
            return Response(
                {'error': f'Error inesperado: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'], url_path='historial')
    def historial_orden(self, request, pk=None):
        """
        Endpoint: GET /api/pagos/{id}/historial/
        
        Obtiene el historial de pagos de una orden de trabajo específica.
        """
        pago = self.get_object()
        pagos_orden = Pago.objects.filter(
            orden_trabajo=pago.orden_trabajo
        ).order_by('-fecha_pago')
        
        serializer = PagoSerializer(pagos_orden, many=True)
        
        return Response({
            'orden_trabajo_id': pago.orden_trabajo.id,
            'total_orden': float(pago.orden_trabajo.total),
            'total_pagado': float(sum(p.monto for p in pagos_orden if p.es_completado())),
            'pagos': serializer.data
        }, status=status.HTTP_200_OK)
