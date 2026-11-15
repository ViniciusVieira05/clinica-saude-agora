"""Consultas usadas pela tela de agendamento online."""
from datetime import timedelta

from django.conf import settings
from django.db.models import Exists, OuterRef
from django.utils import timezone

from apps.agenda.models import HorarioAtendimento
from apps.agenda.services import horarios_livres
from apps.clinica.models import Especialidade, Profissional, Servico

def _profissionais_com_agenda():
    tem_horario = HorarioAtendimento.objects.filter(profissional=OuterRef("pk"), ativo=True)
    return (
        Profissional.objects.filter(ativo=True, usuario__is_active=True)
        .filter(Exists(tem_horario))
        .select_related("usuario")
        .prefetch_related("especialidades")
    )


def especialidades_agendaveis():
    """Especialidades com pelo menos um serviço ativo e um profissional com agenda."""
    return (
        Especialidade.objects.filter(ativo=True, servicos__ativo=True)
        .filter(profissionais__in=_profissionais_com_agenda())
        .distinct()
        .order_by("nome")
    )


def servicos_da_especialidade(especialidade):
    return Servico.objects.filter(especialidade=especialidade, ativo=True).order_by("nome")


def _servico_do_profissional(profissional, especialidade=None, servico=None):
    """Serviço que será mostrado para o profissional, respeitando o filtro escolhido."""
    oferecidos = Servico.objects.filter(ativo=True, especialidade__in=profissional.especialidades.all())
    if profissional.servicos.exists():
        oferecidos = oferecidos.filter(pk__in=profissional.servicos.values("pk"))
    if servico is not None:
        return oferecidos.filter(pk=servico.pk).first()
    if especialidade is not None:
        oferecidos = oferecidos.filter(especialidade=especialidade)
    return oferecidos.order_by("duracao_min", "preco").first()


DIAS_MOSTRADOS = 7


def _periodos(horarios):
    """Separa os horários em Manhã, Tarde e Noite."""
    grupos = [("Manhã", "ph-sun-horizon", []), ("Tarde", "ph-sun", []), ("Noite", "ph-moon", [])]
    for h in horarios:
        hora = timezone.localtime(h).hour
        indice = 0 if hora < 12 else 1 if hora < 18 else 2
        grupos[indice][2].append(h)
    return [{"nome": n, "icone": i, "horarios": hs} for n, i, hs in grupos if hs]


def proximos_dias(profissional, servico):
    hoje = timezone.localdate()
    dias_que_atende = set(
        HorarioAtendimento.objects.filter(profissional=profissional, ativo=True).values_list("dia_semana", flat=True)
    )
    dias = []
    for i in range(settings.AGENDAMENTO_LIMITE_DIAS + 1):
        data = hoje + timedelta(days=i)
        if data.weekday() not in dias_que_atende:
            continue
        livres = horarios_livres(profissional, servico, data)
        if livres:
            dias.append({"data": data, "total": len(livres), "periodos": _periodos(livres)})
        if len(dias) >= DIAS_MOSTRADOS:
            break
    return dias


def agenda_dos_profissionais(especialidade=None, servico=None):
    """Para cada profissional: o serviço mostrado e os próximos dias com horários livres."""
    profissionais = _profissionais_com_agenda().order_by("usuario__nome")
    if especialidade is not None:
        profissionais = profissionais.filter(especialidades=especialidade)

    linhas = []
    for profissional in profissionais:
        servico_mostrado = _servico_do_profissional(profissional, especialidade, servico)
        if servico_mostrado is None:
            continue
        linhas.append({
            "profissional": profissional,
            "servico": servico_mostrado,
            "dias": proximos_dias(profissional, servico_mostrado),
        })
    return linhas
