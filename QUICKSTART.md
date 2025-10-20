# 🚀 Guía Rápida de Despliegue en Railway

## 📝 RESUMEN: Tu proyecto está LISTO para Railway con Docker

### ✅ Archivos creados/actualizados:

1. **Dockerfile** - Configuración del contenedor Docker
2. **.dockerignore** - Archivos excluidos del build
3. **railway.json** - Configuración específica de Railway
4. **settings.py** - Actualizado para producción con ALLOWED_HOSTS y CORS dinámicos
5. **requirements.txt** - Agregado `whitenoise==6.8.2` para archivos estáticos
6. **RAILWAY_DEPLOYMENT.md** - Guía completa paso a paso

---

## 🎯 PASOS RÁPIDOS PARA DESPLEGAR:

### 1️⃣ Preparar Git (si no lo has hecho)

```bash
git init
git add .
git commit -m "Configuración inicial para Railway con Docker"
git remote add origin <tu-url-de-github>
git push -u origin main
```

### 2️⃣ Crear cuenta en Railway

1. Ve a **https://railway.app**
2. Regístrate con GitHub
3. Click en "New Project"
4. Selecciona "Deploy from GitHub repo"
5. Elige tu repositorio `backend-git`

### 3️⃣ Agregar PostgreSQL

1. En tu proyecto Railway, click "+ New"
2. Selecciona "Database" → "PostgreSQL"
3. Railway lo creará automáticamente

### 4️⃣ Configurar Variables de Entorno

En Railway, ve a tu servicio backend → Variables:

```env
SECRET_KEY=8c%m5$y=pws-a_@+hna_h&m$dpg=9y9^luj#p+op#fso1k^j36
DEBUG=False
DATABASE_URL=${{Postgres.DATABASE_URL}}
RAILWAY_PUBLIC_DOMAIN=${{RAILWAY_PUBLIC_DOMAIN}}
```

**Nota:** Las variables con `${{...}}` las auto-completa Railway.

### 5️⃣ ¡Desplegar!

Railway desplegará automáticamente. Verás los logs en tiempo real.

---

## 🔑 Tu SECRET_KEY generada:

```
8c%m5$y=pws-a_@+hna_h&m$dpg=9y9^luj#p+op#fso1k^j36
```

**⚠️ IMPORTANTE:** Copia esta clave y úsala en las variables de Railway.

---

## 📋 Checklist Final:

- [ ] Código subido a GitHub
- [ ] Cuenta de Railway creada
- [ ] Proyecto creado en Railway desde tu repo
- [ ] PostgreSQL agregado
- [ ] Variables de entorno configuradas (SECRET_KEY, DEBUG, DATABASE_URL)
- [ ] Despliegue completado (ver logs)
- [ ] Acceder a tu URL: `https://tu-proyecto.up.railway.app`

---

## 🌐 Configuración de CORS para tu Frontend

Una vez desplegado, tu backend aceptará peticiones de:
- `localhost:3000`, `localhost:5173`, `localhost:5174` (desarrollo local)
- La URL de Railway (automáticamente configurada)

Si tienes un frontend en otro dominio, agrégalo manualmente en `settings.py`:

```python
CORS_ALLOWED_ORIGINS = [
    # ... existentes
    "https://tu-frontend.vercel.app",  # Ejemplo
]
```

---

## 🐛 Solución Rápida de Problemas:

**Error: "Application failed to respond"**
→ Revisa los logs en Railway. Probablemente falta una variable de entorno.

**Error: "Database connection failed"**
→ Asegúrate de que PostgreSQL esté en el mismo proyecto y `DATABASE_URL` configurado.

**Error: "Static files not found"**
→ Ya está solucionado con `whitenoise`. Si persiste, ejecuta en Railway:
```bash
python manage.py collectstatic --noinput
```

---

## 📚 Más información:

Lee el archivo **RAILWAY_DEPLOYMENT.md** para la guía completa con todos los detalles.

---

## 🎉 ¡Eso es todo!

Tu proyecto Django está listo para la nube con:
✅ Docker para portabilidad
✅ PostgreSQL para base de datos
✅ Gunicorn para servidor de producción
✅ WhiteNoise para archivos estáticos
✅ Configuración segura para producción

**¡Feliz despliegue! 🚀**
