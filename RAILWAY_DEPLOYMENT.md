# 🚀 Guía de Despliegue en Railway con Docker

## 📋 Resumen de cambios realizados

Se han creado y configurado los siguientes archivos para el despliegue:

1. **Dockerfile** - Contenedor Docker para tu aplicación
2. **.dockerignore** - Archivos excluidos del build de Docker
3. **railway.json** - Configuración específica de Railway
4. **.gitignore** - Archivos excluidos del repositorio Git
5. **settings.py** - Actualizado con configuración para producción
6. **requirements.txt** - Agregado `whitenoise` para servir archivos estáticos

## 🔧 Pasos para desplegar en Railway

### 1. Preparar el repositorio Git

Si aún no tienes Git inicializado:

```bash
git init
git add .
git commit -m "Configuración inicial para Railway"
```

Si ya tienes Git, solo actualiza:

```bash
git add .
git commit -m "Añadir configuración de Docker y Railway"
git push origin main
```

### 2. Crear cuenta en Railway

1. Ve a [railway.app](https://railway.app)
2. Regístrate con tu cuenta de GitHub
3. Conecta tu repositorio

### 3. Crear un nuevo proyecto en Railway

1. Click en **"New Project"**
2. Selecciona **"Deploy from GitHub repo"**
3. Elige el repositorio `backend-git`
4. Railway detectará automáticamente el Dockerfile

### 4. Agregar una base de datos PostgreSQL

1. En tu proyecto de Railway, haz click en **"+ New"**
2. Selecciona **"Database"** → **"Add PostgreSQL"**
3. Railway creará automáticamente la base de datos

### 5. Configurar las variables de entorno

En el dashboard de Railway, ve a tu servicio backend y agrega estas variables:

**Variables OBLIGATORIAS:**

```env
SECRET_KEY=tu-secret-key-super-seguro-aqui-generado-aleatoriamente
DEBUG=False
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

**Variables OPCIONALES:**

```env
API_KEY_IMGBB=tu-api-key-si-la-necesitas
RAILWAY_PUBLIC_DOMAIN=${{RAILWAY_PUBLIC_DOMAIN}}
```

> **Nota:** Railway auto-completa `DATABASE_URL` cuando agregas PostgreSQL, y `RAILWAY_PUBLIC_DOMAIN` se genera automáticamente.

### 6. Generar una SECRET_KEY segura

Puedes generar una SECRET_KEY ejecutando este comando en tu terminal local:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copia el resultado y úsalo como valor para `SECRET_KEY` en Railway.

### 7. Desplegar

Railway comenzará el despliegue automáticamente. Puedes ver los logs en tiempo real.

El proceso:
1. Construye la imagen Docker
2. Ejecuta las migraciones de Django
3. Inicia el servidor Gunicorn

### 8. Acceder a tu aplicación

Una vez desplegado, Railway te dará una URL como:
```
https://tu-proyecto.up.railway.app
```

## 🔍 Verificar el despliegue

### Verificar la API

Accede a:
```
https://tu-proyecto.up.railway.app/admin/
```

### Ver logs en Railway

En el dashboard de Railway:
1. Selecciona tu servicio
2. Click en la pestaña **"Deployments"**
3. Click en **"View Logs"**

## 🛠️ Comandos útiles

### Ejecutar migraciones manualmente

En Railway, ve a tu servicio → Settings → Deploy y agrega este comando:

```bash
python manage.py migrate
```

### Crear superusuario

Desde Railway CLI (si lo tienes instalado):

```bash
railway run python manage.py createsuperuser
```

O usa el panel de Railway para ejecutar un "One-off Command":

```bash
python manage.py createsuperuser --noinput --username admin --email admin@example.com
```

Luego cambia la contraseña desde el admin de Django.

## 🔐 Seguridad - Lista de verificación

- [ ] `DEBUG=False` en producción
- [ ] `SECRET_KEY` única y segura
- [ ] Base de datos PostgreSQL (no SQLite)
- [ ] `ALLOWED_HOSTS` configurado correctamente
- [ ] CORS configurado para tu dominio frontend
- [ ] Variables de entorno no están en el código

## 🌐 Configurar dominio personalizado (opcional)

1. En Railway, ve a tu servicio
2. Click en **"Settings"** → **"Domains"**
3. Click en **"Generate Domain"** o **"Custom Domain"**
4. Agrega tu dominio personalizado si tienes uno

## 📊 Monitoreo

Railway proporciona:
- Logs en tiempo real
- Métricas de CPU y memoria
- Historial de despliegues
- Reinicio automático en caso de fallos

## 🐛 Solución de problemas comunes

### Error: "Application failed to respond"

- Verifica que el puerto sea `8000`
- Revisa los logs para ver errores específicos

### Error: "Migrations not applied"

- Las migraciones se ejecutan automáticamente con el `startCommand` en `railway.json`
- Verifica los logs de despliegue

### Error: "Database connection failed"

- Asegúrate de que PostgreSQL esté en el mismo proyecto
- Verifica que `DATABASE_URL` esté configurado correctamente

### Error: "Static files not found"

- `whitenoise` maneja los archivos estáticos automáticamente
- Asegúrate de que `STATIC_ROOT` esté configurado en `settings.py`

## 📱 Conectar tu frontend

Una vez desplegado, actualiza tu frontend para usar la URL de Railway:

```javascript
// En tu frontend (React, Vue, etc.)
const API_URL = 'https://tu-proyecto.up.railway.app/api';
```

También actualiza las variables `CORS_ALLOWED_ORIGINS` con la URL de tu frontend en producción.

## 🔄 Actualizaciones futuras

Cada vez que hagas cambios:

```bash
git add .
git commit -m "Descripción de los cambios"
git push origin main
```

Railway detectará los cambios y redesplegará automáticamente.

## 💰 Costos

Railway ofrece:
- **$5 USD** de crédito gratis al mes
- Suficiente para proyectos pequeños/medianos
- Pago por uso después de los créditos gratis

## 📚 Recursos adicionales

- [Documentación de Railway](https://docs.railway.app/)
- [Documentación de Django Deployment](https://docs.djangoproject.com/en/5.2/howto/deployment/)
- [Guía de Docker](https://docs.docker.com/get-started/)

---

## ✅ Checklist final antes de desplegar

- [ ] Archivo `.env.example` creado (sin valores reales)
- [ ] `.gitignore` actualizado
- [ ] `requirements.txt` actualizado con todas las dependencias
- [ ] `Dockerfile` y `.dockerignore` creados
- [ ] `railway.json` configurado
- [ ] `settings.py` preparado para producción
- [ ] Git repository actualizado y pusheado
- [ ] Cuenta de Railway creada
- [ ] PostgreSQL agregado en Railway
- [ ] Variables de entorno configuradas
- [ ] Despliegue exitoso verificado

¡Listo! Tu proyecto Django ahora está en la nube con Railway y Docker 🎉
