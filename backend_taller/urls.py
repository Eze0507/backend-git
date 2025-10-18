"""
URL configuration for backend_taller project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def health_check(request):
    """Health check endpoint para Railway"""
    return JsonResponse({'status': 'ok', 'message': 'Backend is running'})

@csrf_exempt  
def root(request):
    """Root endpoint que redirige al admin"""
    return JsonResponse({
        'message': 'Backend API is running',
        'admin': '/admin/',
        'api': '/api/',
        'health': '/health/'
    })

urlpatterns = [
    path('', root, name='root'),
    path('health/', health_check, name='health_check'),
    path('admin/', admin.site.urls),
    path('api/', include('clientes_servicios.urls')), 
    path('api/', include('personal_admin.urls')),
    path('api/', include('operaciones_inventario.urls')),
]
