"""Guarda o usuário e o IP da requisição atual para a auditoria."""
from contextvars import ContextVar

_usuario_atual = ContextVar("usuario_atual", default=None)
_ip_atual = ContextVar("ip_atual", default=None)


def usuario_atual():
    return _usuario_atual.get()


def ip_atual():
    return _ip_atual.get()


class AuditoriaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        usuario = request.user if getattr(request, "user", None) and request.user.is_authenticated else None
        ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip() or request.META.get("REMOTE_ADDR")
        token_usuario = _usuario_atual.set(usuario)
        token_ip = _ip_atual.set(ip)
        try:
            return self.get_response(request)
        finally:
            _usuario_atual.reset(token_usuario)
            _ip_atual.reset(token_ip)
