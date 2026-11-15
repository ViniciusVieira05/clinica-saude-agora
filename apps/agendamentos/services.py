"""Regras de negócio das consultas (RN03 a RN09)."""
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.agenda.services import horarios_livres

from .models import Consulta


def _validar_janela(inicio):
    """RN04: antecedência mínima e limite máximo de dias."""
    agora = timezone.now()
    if inicio < agora + timedelta(hours=settings.AGENDAMENTO_ANTECEDENCIA_MIN_HORAS):
        raise ValidationError(
            f"Agende com pelo menos {settings.AGENDAMENTO_ANTECEDENCIA_MIN_HORAS} horas de antecedência."
        )
    if inicio > agora + timedelta(days=settings.AGENDAMENTO_LIMITE_DIAS):
        raise ValidationError(f"Só é possível agendar até {settings.AGENDAMENTO_LIMITE_DIAS} dias à frente.")


def _validar_servico(profissional, servico):
    if profissional.servicos.exists() and not profissional.servicos.filter(pk=servico.pk).exists():
        raise ValidationError("Este profissional não atende esse serviço.")


def _salvar(consulta):
    """Grava a consulta; se o banco recusar por sobreposição, devolve um erro amigável."""
    try:
        with transaction.atomic():
            consulta.full_clean(exclude=["criado_por"])
            consulta.save()
    except IntegrityError as erro:
        texto = str(erro)
        if "consulta_sem_sobreposicao_paciente" in texto:
            raise ValidationError("O paciente já tem uma consulta nesse horário.") from erro
        if "consulta_sem_sobreposicao_profissional" in texto:
            raise ValidationError("Esse horário acabou de ser ocupado. Escolha outro.") from erro
        raise
    return consulta


def agendar(*, paciente, profissional, servico, inicio, usuario=None, origem=Consulta.Origem.SITE,
            encaixe=False, observacao=""):
    """Cria uma consulta.

    Encaixe (só recepção) ignora antecedência e a grade de horários livres (RN06),
    mas nunca a sobreposição, que o banco garante.
    """
    _validar_servico(profissional, servico)
    if not encaixe:
        _validar_janela(inicio)
        livres = horarios_livres(profissional, servico, timezone.localtime(inicio).date())
        if inicio not in livres:
            raise ValidationError("Esse horário não está disponível.")

    consulta = Consulta(
        paciente=paciente,
        profissional=profissional,
        servico=servico,
        inicio=inicio,
        fim=inicio + timedelta(minutes=servico.duracao_min),
        preco=servico.preco,  # RN09: preço copiado no momento do agendamento
        origem=origem,
        encaixe=encaixe,
        observacao=observacao,
        criado_por=usuario,
    )
    return _salvar(consulta)


def _validar_prazo_paciente(consulta):
    """RN05: o paciente só altera até X horas antes."""
    limite = consulta.inicio - timedelta(hours=settings.CANCELAMENTO_PRAZO_HORAS)
    if timezone.now() > limite:
        raise ValidationError(
            f"Alterações pelo site só até {settings.CANCELAMENTO_PRAZO_HORAS} horas antes. Fale com a recepção."
        )


def _validar_alteravel(consulta):
    if consulta.status not in (Consulta.Status.AGENDADA, Consulta.Status.CONFIRMADA):
        raise ValidationError("Essa consulta não pode mais ser alterada.")


def cancelar(consulta, *, pela_recepcao=False):
    _validar_alteravel(consulta)
    if not pela_recepcao:
        _validar_prazo_paciente(consulta)
    consulta.status = Consulta.Status.CANCELADA
    consulta.cancelada_em = timezone.now()
    consulta.save(update_fields=["status", "cancelada_em", "atualizado_em"])
    return consulta


def remarcar(consulta, novo_inicio, *, pela_recepcao=False):
    _validar_alteravel(consulta)
    if not pela_recepcao:
        _validar_prazo_paciente(consulta)
        _validar_janela(novo_inicio)
        livres = horarios_livres(
            consulta.profissional,
            consulta.servico,
            timezone.localtime(novo_inicio).date(),
            ignorar_consulta=consulta,
        )
        if novo_inicio not in livres:
            raise ValidationError("Esse horário não está disponível.")
    consulta.inicio = novo_inicio
    consulta.fim = novo_inicio + timedelta(minutes=consulta.servico.duracao_min)
    return _salvar(consulta)


def confirmar(consulta):
    _validar_alteravel(consulta)
    consulta.status = Consulta.Status.CONFIRMADA
    consulta.save(update_fields=["status", "atualizado_em"])
    return consulta


def marcar_realizada(consulta):
    if consulta.status in (Consulta.Status.CANCELADA, Consulta.Status.FALTOU):
        raise ValidationError("Consulta cancelada ou com falta não pode ser marcada como realizada.")
    consulta.status = Consulta.Status.REALIZADA
    consulta.save(update_fields=["status", "atualizado_em"])
    return consulta


def marcar_falta(consulta):
    """RN08: só depois do horário da consulta."""
    if timezone.now() < consulta.inicio:
        raise ValidationError("Só é possível marcar falta depois do horário da consulta.")
    _validar_alteravel(consulta)
    consulta.status = Consulta.Status.FALTOU
    consulta.save(update_fields=["status", "atualizado_em"])
    return consulta


def pode_alterar_pelo_site(consulta):
    """O paciente pode remarcar/cancelar sozinho? (RN05)"""
    if consulta.status not in (Consulta.Status.AGENDADA, Consulta.Status.CONFIRMADA):
        return False
    limite = consulta.inicio - timedelta(hours=settings.CANCELAMENTO_PRAZO_HORAS)
    return timezone.now() <= limite
