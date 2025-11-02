# 💳 Sistema de Pagos con Stripe - Modo Prueba

## 📋 Resumen

Sistema de pagos integrado con Stripe para procesar pagos de prueba de órdenes de trabajo. **SIN webhooks**, confirmación directa desde el frontend.

---

## ✅ Características

- ✅ Pagos directos sin redirección (Stripe Elements)
- ✅ Confirmación inmediata desde el frontend
- ✅ Sin webhooks (ideal para desarrollo/pruebas)
- ✅ Modo de prueba permanente
- ✅ Interfaz amigable con React
- ✅ Validación de pagos en tiempo real

---

## 🔧 Configuración

### 1. Variables de Entorno (Frontend)

Crea o actualiza tu archivo `.env` en el frontend:

```env
# Backend API
VITE_API_URL=http://localhost:8000/api

# Stripe (en modo prueba)
# NO necesitas agregar la publishable key aquí,
# el backend la proporciona automáticamente
```

### 2. Variables de Entorno (Backend - Railway)

En Railway → Variables → Raw Editor:

```env
# Django
DEBUG=False
SECRET_KEY=tu_secret_key_aqui
DATABASE_URL=postgresql://...

# Stripe (SOLO modo prueba)
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 3. Instalar Dependencias (Frontend)

```bash
cd frontend-git
npm install @stripe/stripe-js @stripe/react-stripe-js axios react-icons
```

---

## 📁 Estructura de Archivos

```
frontend-git/src/
├── components/
│   └── pagos/
│       ├── PagarConStripe.jsx       # Componente principal (NUEVO)
│       └── StripePaymentForm.jsx    # Formulario de pago
└── pages/
    └── pagos/
        └── PagoOrdenPage.jsx        # Página de ejemplo (NUEVO)
```

---

## 🚀 Uso

### Opción 1: Usar el componente completo

```jsx
import PagarConStripe from './components/pagos/PagarConStripe';

function MiComponente() {
  const handleSuccess = (data) => {
    console.log('Pago exitoso:', data);
    alert(`¡Pago completado! ID: ${data.pagoId}`);
  };

  return (
    <PagarConStripe
      ordenTrabajoId={123}              // ID de tu orden
      monto="350.00"                    // Monto a mostrar
      ordenNumero="OT-123"              // Número de orden
      onSuccess={handleSuccess}         // Callback de éxito
      onCancel={() => navigate(-1)}    // Callback de cancelación
    />
  );
}
```

### Opción 2: Usar la página completa

```jsx
// En tu router
import PagoOrdenPage from './pages/pagos/PagoOrdenPage';

<Route path="/ordenes/:ordenId/pagar" element={<PagoOrdenPage />} />
```

---

## 🔄 Flujo de Pago

```
1. Usuario hace clic en "Pagar con Tarjeta"
          ↓
2. Frontend llama a: GET /api/pagos/config/
   → Obtiene publishable key de Stripe
          ↓
3. Frontend llama a: POST /api/pagos/create-payment-intent/
   Body: { "orden_trabajo_id": 123 }
   → Backend crea Payment Intent en Stripe
   → Backend crea registro Pago en estado "pendiente"
   → Devuelve { client_secret, payment_intent_id, pago_id }
          ↓
4. Usuario ingresa datos de tarjeta
   Tarjeta de prueba: 4242 4242 4242 4242
          ↓
5. Stripe procesa el pago
   → Si exitoso, status = "succeeded"
          ↓
6. Frontend llama a: GET /api/pagos/verify-payment/?payment_intent_id=pi_xxx
   → Backend verifica con Stripe
   → Backend actualiza Pago a estado "completado"
   → Devuelve { status: "succeeded", pago_id, message }
          ↓
7. Frontend muestra mensaje de éxito
   → Redirige o actualiza la vista
```

---

## 🧪 Tarjetas de Prueba

| Caso | Número | CVV | Fecha | Resultado |
|------|--------|-----|-------|-----------|
| ✅ Éxito | 4242 4242 4242 4242 | 123 | 12/25 | Pago exitoso |
| ❌ Rechazada | 4000 0000 0000 0002 | 123 | 12/25 | Pago rechazado |
| 🔐 3D Secure | 4000 0027 6000 3184 | 123 | 12/25 | Requiere autenticación |

**CVV:** Cualquier 3 dígitos  
**Fecha:** Cualquier mes/año futuro  
**Código postal:** Cualquier número  

---

## 📡 Endpoints del Backend

### 1. Obtener Configuración de Stripe

```
GET /api/pagos/config/
```

**Respuesta:**
```json
{
  "publishableKey": "pk_test_51xxx..."
}
```

### 2. Crear Payment Intent

```
POST /api/pagos/create-payment-intent/
Content-Type: application/json

{
  "orden_trabajo_id": 123
}
```

**Respuesta:**
```json
{
  "client_secret": "pi_xxx_secret_xxx",
  "payment_intent_id": "pi_xxx",
  "pago_id": 456,
  "monto": 350.00
}
```

### 3. Verificar Pago

```
GET /api/pagos/verify-payment/?payment_intent_id=pi_xxx
```

**Respuesta (exitosa):**
```json
{
  "status": "succeeded",
  "orden_trabajo_id": "123",
  "pago_id": 456,
  "message": "Pago confirmado exitosamente"
}
```

---

## 🐛 Solución de Problemas

### Problema: "Stripe no está configurado correctamente"

**Solución:**
- Verifica que las variables `STRIPE_SECRET_KEY` y `STRIPE_PUBLISHABLE_KEY` estén en Railway
- Asegúrate de que las claves empiecen con `sk_test_` y `pk_test_`
- Redespliega el backend en Railway

### Problema: "El monto de la orden debe ser mayor a 0"

**Solución:**
- Verifica que tu modelo `OrdenTrabajo` tenga el campo `costo_total`
- Asegúrate de que la orden tenga un monto asignado antes de intentar pagar

### Problema: CardElement no se muestra

**Solución:**
```bash
# Reinstalar dependencias de Stripe
npm install @stripe/stripe-js @stripe/react-stripe-js --force
```

### Problema: Error de CORS

**Solución:**
En `backend-git/backend_taller/settings.py`, verifica:
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "https://frontend-git-production.up.railway.app",
]
```

---

## 🔍 Verificar que Funciona

### 1. Prueba el endpoint de config:

Abre en tu navegador:
```
https://backend-git-production.up.railway.app/api/pagos/config/
```

Deberías ver:
```json
{"publishableKey": "pk_test_51xxx..."}
```

### 2. Revisa los logs del navegador (F12):

```
✅ Stripe inicializado
✅ Publishable key obtenida
💳 Creando Payment Intent para orden: 123
✅ Payment Intent creado
```

### 3. Completa un pago de prueba:

1. Ve a la página de pago
2. Usa tarjeta: `4242 4242 4242 4242`
3. CVV: `123`
4. Fecha: `12/25`
5. Haz clic en "Pagar"
6. Deberías ver: "¡Pago Exitoso!"

---

## 📊 Ver Pagos en Stripe Dashboard

1. Ve a: https://dashboard.stripe.com/test/payments
2. Deberías ver los pagos de prueba listados
3. Click en cualquier pago para ver detalles
4. Verifica los metadata (orden_trabajo_id)

---

## 🎓 Notas para Proyecto Universitario

- ✅ Este sistema usa **SOLO modo de prueba** de Stripe
- ✅ No procesa pagos reales
- ✅ Ideal para demostrar funcionalidad sin riesgos
- ✅ Los pagos se registran en tu base de datos
- ✅ Puedes mostrar el historial de pagos

---

## 📝 Próximos Pasos (Opcional)

Si en el futuro quieres mejorar el sistema:

1. **Agregar webhooks** para mayor confiabilidad
2. **Implementar reembolsos** desde el admin
3. **Historial de pagos por cliente**
4. **Reportes de pagos** en PDF
5. **Notificaciones por email** al completar pagos

---

## 🆘 Soporte

Si tienes problemas:

1. Revisa los logs del navegador (F12 → Console)
2. Revisa los logs de Railway (Deployments → Logs)
3. Verifica que las claves de Stripe estén correctamente configuradas
4. Asegúrate de usar la tarjeta de prueba correcta

---

## ✅ Checklist Final

- [ ] Variables de Stripe configuradas en Railway
- [ ] Frontend puede obtener publishable key
- [ ] Se puede crear un Payment Intent
- [ ] CardElement se muestra correctamente
- [ ] Pago con tarjeta de prueba funciona
- [ ] El pago se verifica y se marca como completado
- [ ] El registro se guarda en la base de datos

¡Listo! Tu sistema de pagos con Stripe está funcionando. 🎉
