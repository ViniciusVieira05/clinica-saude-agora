from django.conf import settings


def clinica(request):
    """Deixa os dados da clínica disponíveis em todos os templates como {{ clinica }}."""
    return {"clinica": settings.CLINICA}
