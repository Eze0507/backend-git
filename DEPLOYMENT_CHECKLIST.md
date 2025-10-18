# ✅ Checklist de Despliegue Railway

## 📋 Antes de comenzar

- [ ] Tengo cuenta en GitHub
- [ ] Mi código está en un repositorio de GitHub
- [ ] He leído QUICKSTART.md
- [ ] Tengo Docker instalado (opcional, para pruebas locales)

---

## 🔧 Configuración del Proyecto

### Archivos necesarios (Ya creados ✅)
- [x] `Dockerfile`
- [x] `.dockerignore`
- [x] `railway.json`
- [x] `.gitignore`
- [x] `.env.example`
- [x] `requirements.txt` (con whitenoise y gunicorn)
- [x] `settings.py` (configurado para producción)

---

## 🚀 Proceso de Despliegue

### Paso 1: Preparar Git
- [ ] Todos los cambios están commiteados
  ```bash
  git status  # Verificar estado
  git add .
  git commit -m "Listo para Railway"
  ```
- [ ] Código subido a GitHub
  ```bash
  git push origin main
  ```

### Paso 2: Railway - Crear Cuenta
- [ ] Ir a https://railway.app
- [ ] Registrarse con GitHub
- [ ] Conectar cuenta de GitHub

### Paso 3: Railway - Crear Proyecto
- [ ] Click en "New Project"
- [ ] Seleccionar "Deploy from GitHub repo"
- [ ] Elegir repositorio: `backend-git`
- [ ] Railway detecta Dockerfile automáticamente

### Paso 4: Railway - Agregar PostgreSQL
- [ ] Click en "+ New" en el proyecto
- [ ] Seleccionar "Database" → "PostgreSQL"
- [ ] Esperar a que se cree (1-2 minutos)

### Paso 5: Railway - Variables de Entorno
- [ ] Ir al servicio backend
- [ ] Click en "Variables"
- [ ] Agregar las siguientes variables:

#### Variables OBLIGATORIAS:
```env
✅ SECRET_KEY
   Valor: 8c%m5$y=pws-a_@+hna_h&m$dpg=9y9^luj#p+op#fso1k^j36
   (O genera una nueva con: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")

✅ DEBUG
   Valor: False

✅ DATABASE_URL
   Valor: ${{Postgres.DATABASE_URL}}
   (Railway lo auto-completa)

✅ RAILWAY_PUBLIC_DOMAIN
   Valor: ${{RAILWAY_PUBLIC_DOMAIN}}
   (Railway lo auto-completa)
```

#### Variables OPCIONALES:
```env
⭕ API_KEY_IMGBB
   Valor: tu-api-key-si-la-usas
```

### Paso 6: Railway - Desplegar
- [ ] Railway inicia el despliegue automáticamente
- [ ] Ver logs en tiempo real
- [ ] Esperar mensaje: "Build successful"
- [ ] Esperar mensaje: "Deployment successful"

### Paso 7: Verificar Despliegue
- [ ] Click en la URL generada (algo como: `https://backend-taller-production.up.railway.app`)
- [ ] Verificar que el servidor responde
- [ ] Probar endpoint: `/admin/` (debe mostrar login de Django)

---

## 🧪 Pruebas Post-Despliegue

### Verificar Admin de Django
- [ ] Acceder a: `https://tu-dominio.railway.app/admin/`
- [ ] Debe mostrar la página de login

### Crear Superusuario
- [ ] En Railway, ir a tu servicio
- [ ] Click en "..." → "Run a command"
- [ ] Ejecutar:
  ```bash
  python manage.py createsuperuser --noinput --username admin --email admin@example.com
  ```
- [ ] Cambiar contraseña desde el admin

### Probar API
- [ ] Probar endpoint de autenticación:
  ```bash
  POST https://tu-dominio.railway.app/api/token/
  ```
- [ ] Verificar respuesta exitosa

---

## 🔐 Seguridad Final

- [ ] `DEBUG=False` en Railway
- [ ] `SECRET_KEY` es única y no está en el código
- [ ] `.env` está en `.gitignore`
- [ ] Base de datos es PostgreSQL (no SQLite)
- [ ] HTTPS está activo (Railway lo da gratis)
- [ ] CORS configurado para dominios específicos

---

## 🌐 Configuración Frontend (Si aplica)

### Actualizar URL del Backend en Frontend
- [ ] Cambiar URL de API en frontend:
  ```javascript
  const API_URL = 'https://tu-dominio.railway.app';
  ```

### Agregar dominio del frontend a CORS
- [ ] Desplegar frontend (Vercel, Netlify, etc.)
- [ ] Agregar dominio del frontend a variables de Railway:
  ```env
  FRONTEND_URL=https://tu-frontend.vercel.app
  ```
- [ ] Actualizar `settings.py` si es necesario

---

## 📊 Monitoreo

### Railway Dashboard
- [ ] Revisar métricas de CPU
- [ ] Revisar métricas de memoria
- [ ] Configurar alertas (opcional)

### Logs
- [ ] Saber cómo acceder a logs: Dashboard → Deployments → View Logs
- [ ] Revisar logs periódicamente para errores

---

## 💰 Costos

- [ ] Entender el plan gratuito de Railway: $5 USD/mes de crédito gratis
- [ ] Monitorear uso para evitar cargos inesperados
- [ ] Considerar plan pago si es necesario

---

## 🎉 ¡Completado!

Si marcaste todas las casillas, ¡tu proyecto está en producción!

### Próximos pasos opcionales:
- [ ] Configurar dominio personalizado
- [ ] Configurar backups automáticos de DB
- [ ] Implementar CI/CD avanzado
- [ ] Agregar monitoreo con Sentry
- [ ] Configurar emails (SendGrid, etc.)

---

## 🆘 Si algo sale mal...

### Recursos de ayuda:
1. **Logs de Railway** - Siempre revisa los logs primero
2. **RAILWAY_DEPLOYMENT.md** - Guía detallada con soluciones
3. **Documentación Railway** - https://docs.railway.app
4. **Comunidad Railway** - Discord de Railway

### Problemas comunes:
- **Build falla**: Revisa el Dockerfile y requirements.txt
- **App no responde**: Verifica variables de entorno
- **Error de DB**: Asegúrate de que PostgreSQL esté agregado
- **502 Bad Gateway**: Revisa logs, probablemente error en settings.py

---

**¡Suerte con tu despliegue! 🚀**

Recuerda: El primer despliegue siempre toma más tiempo. ¡Ten paciencia!
