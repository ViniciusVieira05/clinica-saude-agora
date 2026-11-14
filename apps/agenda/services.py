"""Cálculo de horários livres (RN01 e RN02)."""
from datetime import datetime, timedelta

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from .models import Bloqueio, HorarioAtendimento


def _aware(data, hora):
    return timezone.make_aware(datetime.combine(data, hora), timezone.get_current_timezone())


def _sobrepoe(inicio_a, fim_a, inicio_b, fim_b):
    return inicio_a < fim_b and inicio_b < fim_a


def horarios_livres(profissional, servico, data, *, respeitar_antecedencia=True, ignorar_consulta=None):
    """Lista os horários de início livres de um profissional em uma data, para um serviço.

    - Gera horários a cada `servico.duracao_min` dentro do expediente (RN02).
    - Remove intervalo, bloqueios e consultas já marcadas (RN01).
    - Com `respeitar_antecedencia`, remove horários antes da antecedência mínima (RN04).
    - `ignorar_consulta`: usada ao remarcar, para não contar a própria consulta como ocupada.
    """
    from apps.agendamentos.models import Consulta  # evita import circular

    expediente = HorarioAtendimento.objects.filter(
        profissional=profissional, dia_semana=data.weekday(), ativo=True
    ).first()
    if not expediente:
        return []

    duracao = timedelta(minutes=servico.duracao_min)
    inicio_dia = _aware(data, expediente.hora_inicio)
    fim_dia = _aware(data, expediente.hora_fim)

    ocupados = []
    if expediente.intervalo_inicio and expediente.intervalo_fim:
        ocupados.append((_aware(data, expediente.intervalo_inicio), _aware(data, expediente.intervalo_fim)))

    bloqueios = Bloqueio.objects.filter(
        Q(profissional=profissional) | Q(profissional__isnull=True),
        ativo=True,
        inicio__lt=fim_dia,
        fim__gt=inicio_dia,
    ).values_list("inicio", "fim")
    ocupados.extend(bloqueios)

    consultas = Consulta.objects.filter(
        profissional=profissional, inicio__lt=fim_dia, fim__gt=inicio_dia
    ).exclude(status=Consulta.Status.CANCELADA)
    if ignorar_consulta is not None:
        consultas = consultas.exclude(pk=ignorar_consulta.pk)
    ocupados.extend(consultas.values_list("inicio", "fim"))

    agora = timezone.now()
    minimo = agora
    if respeitar_antecedencia:
        minimo = agora + timedelta(hours=settings.AGENDAMENTO_ANTECEDENCIA_MIN_HORAS)

    livres = []
    slot = inicio_dia
    while slot + duracao <= fim_dia:
        fim_slot = slot + duracao
        livre = slot >= minimo and not any(_sobrepoe(slot, fim_slot, i, f) for i, f in ocupados)
        if livre:
            livres.append(slot)
        slot += duracao
    return livres
