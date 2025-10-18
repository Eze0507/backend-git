from pathlib import Path
from decouple import config
import dj_database_url
import os
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
#SECRET_KEY = config('SECRET_KEY') <---Antes porque daba error en despliegue
SECRET_KEY = config('DJANGO_SECRET_KEY', default='u8f4a3^d*t%u=*m9cz35#3k7j__pazi_ey%*c3(2)nj*%=#n&&')
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

# Configuración de ALLOWED_HOSTS para Railway
RAILWAY_PUBLIC_DOMAIN = config('RAILWAY_PUBLIC_DOMAIN', default='')
ALLOWED_HOSTS = ["192.168.0.3", "localhost", "127.0.0.1"]
if RAILWAY_PUBLIC_DOMAIN:
    ALLOWED_HOSTS.append(RAILWAY_PUBLIC_DOMAIN)
    # También permitir el dominio de Railway sin www
    ALLOWED_HOSTS.append(f'*.railway.app')

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_seed',

    # Tus apps
    'personal_admin',
    'clientes_servicios',
    'finanzas_facturacion',
    'operaciones_inventario',
    'django_filters', 

    # Paquetes externos
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
]

# DRF / Authentication
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",   # Bearer
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.AllowAny",  # todo requiere auth por defecto
    ),
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
}

# JWT Configuration
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Para servir archivos estáticos
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',  
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend_taller.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend_taller.wsgi.application'

# Database
POSTGRES_FALLBACK_URL = 'postgres://user:password@localhost:5432/mydatabase'

DATABASES = {
    # Al quitar el valor de respaldo, forzamos a Railway a usar su variable.
    # Si por alguna razón falla, dj_database_url puede manejar la cadena vacía
    # O, como ya resolvimos todos los errores, la variable REAL de Railway DEBE ser inyectada.
    'default': dj_database_url.config(default=config('DJANGO_DATABASE_URL')) 
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/La_Paz'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Configuración de WhiteNoise para archivos estáticos
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS: permitir peticiones desde tu frontend local (ej: React en puerto 5173 o 3000)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]

# Agregar dominio de Railway si existe
if RAILWAY_PUBLIC_DOMAIN:
    CORS_ALLOWED_ORIGINS.extend([
        f"https://{RAILWAY_PUBLIC_DOMAIN}",
        f"http://{RAILWAY_PUBLIC_DOMAIN}",
    ])

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]

# Agregar dominio de Railway a CSRF trusted origins
if RAILWAY_PUBLIC_DOMAIN:
    CSRF_TRUSTED_ORIGINS.extend([
        f"https://{RAILWAY_PUBLIC_DOMAIN}",
        f"http://{RAILWAY_PUBLIC_DOMAIN}",
    ])

CORS_ALLOW_ALL_ORIGINS = False 

# Permitir que el navegador envíe cookies en peticiones cross-origin
CORS_ALLOW_CREDENTIALS = True
API_KEY_IMGBB= config('API_KEY_IMGBB', default='')