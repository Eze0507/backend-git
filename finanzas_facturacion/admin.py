from django.contrib import admin
from .models import Pago


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ['id', 'orden_trabajo', 'monto', 'metodo_pago', 'estado', 'fecha_pago', 'usuario']
    list_filter = ['estado', 'metodo_pago', 'fecha_pago']
    search_fields = ['orden_trabajo__id', 'stripe_payment_intent_id', 'numero_referencia']
    readonly_fields = ['fecha_pago', 'fecha_actualizacion', 'stripe_payment_intent_id']
    
    fieldsets = (
        ('Información de Pago', {
            'fields': ('orden_trabajo', 'monto', 'metodo_pago', 'estado', 'usuario')
        }),
        ('Stripe', {
            'fields': ('stripe_payment_intent_id', 'currency'),
            'classes': ('collapse',)
        }),
        ('Detalles Adicionales', {
            'fields': ('descripcion', 'numero_referencia', 'fecha_pago', 'fecha_actualizacion')
        }),
    )
