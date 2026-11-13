"""
Mixins y decoradores de Control de Acceso Basado en Roles (RBAC).
"""
from functools import wraps
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


class RolRequeridoMixin(LoginRequiredMixin):
    """
    Mixin para vistas basadas en clase (CBV).
    Uso:
        class MiVista(RolRequeridoMixin, View):
            roles_permitidos = ['ADMIN', 'DOCENTE']
    """
    roles_permitidos = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)  # LoginRequiredMixin redirige
        if (
            self.roles_permitidos
            and not request.user.is_superuser
            and request.user.rol not in self.roles_permitidos
        ):
            raise PermissionDenied("No tienes permiso para acceder a esta sección.")
        return super().dispatch(request, *args, **kwargs)


def rol_requerido(*roles):
    """
    Decorador para vistas funcionales (FBV).
    Uso:
        @rol_requerido('ADMIN', 'RECEPCION')
        def mi_vista(request): ...
    """
    def decorador(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_superuser and request.user.rol not in roles:
                raise PermissionDenied("No tienes permiso para acceder a esta sección.")
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorador