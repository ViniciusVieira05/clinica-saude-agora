from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from . import selectors


def inicio(request):
    proximo = selectors.proximo_horario_disponivel()
    contexto = {
        "especialidades": selectors.especialidades_em_destaque(),
        "profissionais": selectors.profissionais_ativos()[:4],
        "proximo": proximo,
        "proximo_eh_hoje": bool(proximo) and timezone.localtime(proximo["inicio"]).date() == timezone.localdate(),
        "convenios": selectors.convenios(),
        "fotos": selectors.fotos_clinica(),
        "avaliacoes": selectors.avaliacoes(),
        "perguntas": selectors.perguntas_frequentes(),
        "orientacoes": selectors.orientacoes_publicadas()[:3],
    }
    return render(request, "site_publico/inicio.html", contexto)


def orientacoes(request):
    pagina = Paginator(selectors.orientacoes_publicadas(), 9).get_page(request.GET.get("pagina"))
    return render(request, "site_publico/orientacoes.html", {"pagina": pagina})


def orientacao(request, slug):
    item = get_object_or_404(selectors.orientacoes_publicadas(), slug=slug)
    outras = selectors.orientacoes_publicadas().exclude(pk=item.pk)[:3]
    return render(request, "site_publico/orientacao.html", {"item": item, "outras": outras})


def privacidade(request):
    return render(request, "site_publico/privacidade.html")


def termos(request):
    return render(request, "site_publico/termos.html")


def profissional(request, pk):
    from apps.agendamentos import selectors as agenda

    pessoa = get_object_or_404(selectors.profissionais_ativos(), pk=pk)
    servico = agenda._servico_do_profissional(pessoa)
    linha = None
    if servico:
        linha = {"profissional": pessoa, "servico": servico, "dias": agenda.proximos_dias(pessoa, servico)}
    servicos = agenda.servicos_do_profissional(pessoa)
    return render(request, "site_publico/profissional.html", {"pessoa": pessoa, "linha": linha, "servicos": servicos})
