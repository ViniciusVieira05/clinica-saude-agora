from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

from apps.contas.models import Usuario

PERFIS_RECEPCAO = (Usuario.Tipo.RECEPCAO, Usuario.Tipo.ADMIN)


def eh_recepcao(usuario):
    return usuario.is_authenticated and (usuario.is_superuser or usuario.tipo in PERFIS_RECEPCAO)


def recepcao_required(view):
    """Só recepção e administrador entram. Quem não está logado vai para o login."""

    @wraps(view)
    def _view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not eh_recepcao(request.user):
            raise PermissionDenied
        return view(request, *args, **kwargs)

    return _view
