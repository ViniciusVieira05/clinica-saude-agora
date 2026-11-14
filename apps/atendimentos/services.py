"""Registro do atendimento pelo profissional."""
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.agendamentos import services as consultas
from apps.agendamentos.models import Consulta

from .models import Atendimento


@transaction.atomic
def registrar_atendimento(consulta, *, observacoes="", retorno_sugerido_em=None, usuario=None):
    """Cria (ou atualiza) o atendimento e marca a consulta como realizada."""
    if consulta.status in (Consulta.Status.CANCELADA, Consulta.Status.FALTOU):
        raise ValidationError("Não é possível registrar atendimento de consulta cancelada ou com falta.")
    atendimento, _ = Atendimento.objects.update_or_create(
        consulta=consulta,
        defaults={
            "observacoes": observacoes,
            "retorno_sugerido_em": retorno_sugerido_em,
            "registrado_por": usuario,
        },
    )
    if consulta.status != Consulta.Status.REALIZADA:
        consultas.marcar_realizada(consulta)
    return atendimento
