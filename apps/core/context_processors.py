from django.conf import settings


def clinica(request):
    """Dados da clínica e se o sistema está em modo demonstração, em todos os templates."""
    return {"clinica": settings.CLINICA, "modo_demo": getattr(settings, "DEMO", False)}
