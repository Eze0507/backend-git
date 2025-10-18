# 🚗 ERP para Taller Mecánico

Sistema de gestión empresarial (ERP) desarrollado con Django REST Framework para la administración de talleres mecánicos.

## 🌟 Características

- 👥 Gestión de personal y administración
- 🚙 Control de clientes y servicios
- 📦 Operaciones e inventario
- 💰 Finanzas y facturación
- 🔐 Autenticación JWT
- 📊 API RESTful

---

## 🚀 Despliegue en Railway (Recomendado)

Este proyecto está configurado para desplegarse en Railway con Docker. Lee las guías:

- **[QUICKSTART.md](QUICKSTART.md)** - Guía rápida (5 minutos)
- **[RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md)** - Guía completa detallada

---

## 💻 Desarrollo Local

### Clonar repositorio
```bash
git clone [repository url]
cd Backend-taller
```

### 1. Crear entorno virtual

**Windows:**
```bash
python -m venv env
.\env\Scripts\activate
```

**macOS/Linux:**
```bash
python -m venv env
source env/bin/activate
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
SECRET_KEY=tu-secret-key-aqui
DEBUG=True
DATABASE_URL=postgresql://user:password@localhost/dbname
API_KEY_IMGBB=tu-api-key-opcional
```

**Generar SECRET_KEY:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 4. Ejecutar migraciones
```bash
python manage.py migrate
```

**Nota:** Si hay conflictos con las migraciones:
```bash
python manage.py makemigrations --merge
# Presiona 'y' cuando pregunte
```

### 5. Crear superusuario (opcional)
```bash
python manage.py createsuperuser
```

### 6. Iniciar servidor
```bash
python manage.py runserver
```

Accede a: http://localhost:8000

---

## 🐳 Desarrollo con Docker (Opcional)

### Opción 1: Docker Compose (Recomendado para desarrollo)

```bash
docker-compose up --build
```

Esto iniciará:
- PostgreSQL en puerto 5432
- Django en puerto 8000

### Opción 2: Solo Docker

```bash
docker build -t backend-taller .
docker run -p 8000:8000 --env-file .env backend-taller
```

---

## 📦 Estructura del Proyecto

```
Backend-taller/
├── backend_taller/          # Configuración principal
├── personal_admin/          # Módulo de personal
├── clientes_servicios/      # Módulo de clientes
├── operaciones_inventario/  # Módulo de inventario
├── finanzas_facturacion/    # Módulo de finanzas
├── Dockerfile               # Configuración Docker
├── docker-compose.yml       # Docker Compose para desarrollo
├── railway.json             # Configuración Railway
└── requirements.txt         # Dependencias Python
```

---

## 🔧 Tecnologías

- **Django 5.2.6**
- **Django REST Framework 3.16.1**
- **PostgreSQL** (psycopg2-binary)
- **JWT Authentication** (simplejwt)
- **Gunicorn** (servidor WSGI)
- **WhiteNoise** (archivos estáticos)
- **Docker** (contenedorización)

---

## 📚 API Endpoints

### Autenticación
- `POST /api/token/` - Obtener token
- `POST /api/token/refresh/` - Refrescar token

### Clientes y Servicios
- `GET/POST /api/clientes/`
- `GET/PUT/DELETE /api/clientes/{id}/`

### Inventario
- `GET/POST /api/items/`
- `GET/POST /api/areas/`
- `GET/POST /api/vehiculos/`

*Ver documentación completa de endpoints en el admin de Django.*

---

## 🔄 Actualizar Dependencias

```bash
pip freeze > requirements.txt
```

---

## 📤 SUBIR PROYECTO A GITHUB


### 1. Actualizar dependencias (si es necesario)
```bash
pip freeze > requirements.txt
```

### 2. Agregar cambios
```bash
git add .
git commit -m "mensaje descriptivo del cambio"
```

### 3. Sincronizar con remoto
```bash
git pull origin main
```

### 4. Si hay conflictos
Resuelve los conflictos manualmente en tu editor (VS Code, GitHub Desktop, etc.)

```bash
git add .
git commit -m "Conflictos resueltos"
git push origin main
```

### 5. Si no hay conflictos
```bash
git push origin main
```

---

## 🌐 Despliegue en Producción

### Railway (Recomendado)
1. Lee **[QUICKSTART.md](QUICKSTART.md)** para pasos rápidos
2. Sigue **[RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md)** para guía completa

### Características del despliegue:
✅ Docker para portabilidad  
✅ PostgreSQL automático  
✅ HTTPS incluido  
✅ CI/CD automático  
✅ Variables de entorno seguras  

---

## 🛠️ Scripts Útiles

### Verificar configuración para Railway
```powershell
.\verify-deploy.ps1
```

### Construir imagen Docker localmente
```powershell
.\build-docker.ps1
```

---

## 🤝 Contribuir

1. Fork el proyecto
2. Crea tu rama (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 📝 Licencia

Este proyecto es privado y de uso interno.

---

## 👥 Equipo

Desarrollado por el equipo de ProyectoSI2

---

## 📞 Soporte

Para problemas o preguntas, abre un issue en el repositorio.

---

**¡Gracias por usar nuestro ERP para Taller Mecánico! 🚀**


