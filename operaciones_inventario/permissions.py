from rest_framework import permissions

class IsClienteReadOnlyOrFullAccess(permissions.BasePermission):
    """
    Permiso personalizado que:
    - Otorga permisos de solo lectura (GET, HEAD, OPTIONS) a CUALQUIER usuario autenticado.
    - Otorga permisos de escritura (POST, PUT, PATCH, DELETE) SOLO a usuarios 
      autenticados que NO estén en el grupo 'cliente'.
      (Ej. 'administrador', 'empleado').
    """

    def has_permission(self, request, view):
        # Si el método es de solo lectura (GET, etc.), todos los autenticados pueden ver.
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Si el método es de escritura (POST, PUT, etc.),
        # necesitamos verificar que el usuario NO sea un cliente.
        
        # Si no está autenticado, no tiene permiso.
        if not request.user or not request.user.is_authenticated:
            return False
            
        # Verifica si el usuario pertenece al grupo 'cliente'.
        is_cliente = request.user.groups.filter(name='cliente').exists()
        
        # Si es cliente, NO tiene permiso de escritura (return False).
        # Si NO es cliente (es admin/empleado), SÍ tiene permiso (return True).
        return not is_cliente