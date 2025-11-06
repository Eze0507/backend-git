from rest_framework import permissions

class IsClienteReadOnlyOrFullAccess(permissions.BasePermission):
    """
    Permiso personalizado que:
    - Otorga permisos de solo lectura (GET, HEAD, OPTIONS) a CUALQUIER usuario autenticado.
    - Otorga permisos de escritura (POST, PUT, PATCH, DELETE) SOLO a usuarios 
      autenticados que NO estén en el grupo 'cliente'.
      (Ej. 'administrador', 'empleado').
    - EXCEPCIÓN: Permite POST (crear órdenes) a usuarios del grupo 'cliente'.
    """

    def has_permission(self, request, view):
        # Si el método es de solo lectura (GET, etc.), todos los autenticados pueden ver.
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Si no está autenticado, no tiene permiso.
        if not request.user or not request.user.is_authenticated:
            return False
            
        # Verifica si el usuario pertenece al grupo 'cliente'.
        is_cliente = request.user.groups.filter(name='cliente').exists()
        
        # EXCEPCIÓN: Permitir a clientes CREAR órdenes (POST) desde la app móvil
        # pero NO modificar o eliminar
        if request.method == 'POST' and view.__class__.__name__ == 'OrdenTrabajoViewSet':
            return True  # Todos los usuarios autenticados pueden crear órdenes
        
        # Para otros métodos de escritura (PUT, PATCH, DELETE),
        # Si es cliente, NO tiene permiso (return False).
        # Si NO es cliente (es admin/empleado), SÍ tiene permiso (return True).
        return not is_cliente