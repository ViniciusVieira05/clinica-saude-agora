"""Consultas usadas pelas páginas públicas."""
from datetime import timedelta

from django.db.models import Prefetch
from django.utils import timezone

from apps.agenda.services import horarios_livres
from apps.clinica.models import Especialidade, Profissional, Servico

from .models import Avaliacao, Convenio, FotoClinica, Orientacao, PerguntaFrequente


def especialidades_em_destaque(limite=4):
    return Especialidade.objects.filter(ativo=True).prefetch_related(
        Prefetch("servicos", queryset=Servico.objects.filter(ativo=True))
    )[:limite]


def profissionais_ativos():
    return (
        Profissional.objects.filter(ativo=True, usuario__is_active=True)
        .select_related("usuario")
        .prefetch_related("especialidades")
    )


def _servico_padrao(profissional):
    servico = profissional.servicos.filter(ativo=True).order_by("duracao_min").first()
    if servico:
        return servico
    return Servico.objects.filter(
        ativo=True, especialidade__in=profissional.especialidades.all()
    ).order_by("duracao_min").first()


def proximo_horario_disponivel(dias=7):
    """Primeiro horário livre entre todos os profissionais nos próximos dias."""
    profissionais = [p for p in profissionais_ativos().filter(horarios__ativo=True).distinct()]
    hoje = timezone.localdate()
    for i in range(dias):
        data = hoje + timedelta(days=i)
        melhor = None
        for profissional in profissionais:
            servico = _servico_padrao(profissional)
            if not servico:
                continue
            livres = horarios_livres(profissional, servico, data)
            if livres and (melhor is None or livres[0] < melhor["inicio"]):
                melhor = {"inicio": livres[0], "profissional": profissional}
        if melhor:
            return melhor
    return None


def convenios():
    return Convenio.objects.filter(ativo=True)


def fotos_clinica():
    return FotoClinica.objects.filter(ativo=True)


def avaliacoes(limite=3):
    return Avaliacao.objects.filter(ativo=True)[:limite]


def perguntas_frequentes():
    return PerguntaFrequente.objects.filter(ativo=True)


def orientacoes_publicadas():
    return Orientacao.objects.filter(ativo=True)
