import time

from django.conf import settings

# Muda a cada vez que o servidor reinicia: força o navegador a baixar o CSS/JS novo.
VERSAO_ESTATICOS = str(int(time.time()))


def clinica(request):
    """Dados da clínica, modo demonstração e versão dos arquivos estáticos, em todos os templates."""
    return {
        "clinica": settings.CLINICA,
        "modo_demo": getattr(settings, "DEMO", False),
        "versao": VERSAO_ESTATICOS,
    }
