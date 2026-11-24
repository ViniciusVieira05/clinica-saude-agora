from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.agenda.services import horarios_livres
from apps.agendamentos import selectors as agenda_selectors
from apps.agendamentos import services as consultas
from apps.agendamentos.models import Consulta
from apps.clinica.models import Profissional, Servico
from apps.financeiro import services as financeiro
from apps.financeiro.models import Pagamento
from apps.pacientes.models import Paciente

from . import selectors
from .forms import PacienteForm
from .permissoes import recepcao_required


def _int(valor):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def _data(valor, padrao=None):
    try:
        return datetime.strptime(valor, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return padrao


def _profissionais():
    return Profissional.objects.filter(ativo=True).select_related("usuario").order_by("usuario__nome")


# ---------------- Agenda do dia ----------------

@recepcao_required
def agenda(request):
    hoje = timezone.localdate()
    data = _data(request.GET.get("data"), hoje)
    profissionais = _profissionais()
    profissional = profissionais.filter(pk=_int(request.GET.get("profissional"))).first()

    lista = selectors.anotar_pagamento(list(selectors.consultas_do_dia(data, profissional)))
    ativas = [c for c in lista if c.status != Consulta.Status.CANCELADA]
    canceladas = [c for c in lista if c.status == Consulta.Status.CANCELADA]

    def link(d):
        params = {"data": d.isoformat()}
        if profissional:
            params["profissional"] = profissional.pk
        return "?" + urlencode(params)

    contexto = {
        "data": data,
        "hoje": hoje,
        "profissionais": profissionais,
        "profissional": profissional,
        "consultas": ativas,
        "canceladas": canceladas,
        "resumo": selectors.resumo_do_dia(lista),
        "link_anterior": link(data - timedelta(days=1)),
        "link_proximo": link(data + timedelta(days=1)),
        "link_hoje": link(hoje),
        "formas_pagamento": Pagamento.Forma.choices,
    }
    return render(request, "painel/agenda.html", contexto)


def _responder_linha(request, consulta):
    """Com HTMX devolve só a linha atualizada; sem HTMX volta para a agenda do dia."""
    if request.htmx:
        consulta = selectors.anotar_pagamento([
            Consulta.objects.select_related("paciente", "profissional__usuario", "servico")
            .prefetch_related("pagamentos").get(pk=consulta.pk)
        ])[0]
        return render(request, "painel/_linha_consulta.html", {
            "c": consulta, "formas_pagamento": Pagamento.Forma.choices, "hoje": timezone.localdate(),
        })
    data = timezone.localtime(consulta.inicio).date().isoformat()
    return redirect(reverse("painel:agenda") + f"?data={data}")


ACOES = {
    "confirmar": (consultas.confirmar, "Presença confirmada."),
    "realizada": (consultas.marcar_realizada, "Atendimento marcado como realizado."),
    "falta": (consultas.marcar_falta, "Falta registrada."),
    "cancelar": (lambda c: consultas.cancelar(c, pela_recepcao=True), "Consulta cancelada."),
}


@require_POST
@recepcao_required
def acao(request, pk, nome):
    consulta = get_object_or_404(Consulta, pk=pk)
    if nome not in ACOES:
        return redirect("painel:agenda")
    funcao, texto = ACOES[nome]
    try:
        funcao(consulta)
        messages.success(request, texto)
    except ValidationError as erro:
        messages.error(request, " ".join(erro.messages))
    return _responder_linha(request, consulta)


@require_POST
@recepcao_required
def pagamento(request, pk):
    consulta = get_object_or_404(Consulta, pk=pk)
    try:
        valor = Decimal(request.POST.get("valor", "").replace(",", "."))
    except InvalidOperation:
        valor = Decimal("0")
    try:
        financeiro.registrar_pagamento(
            consulta, valor=valor, forma=request.POST.get("forma", ""), usuario=request.user
        )
        messages.success(request, f"Pagamento de R$ {valor:.2f} registrado.")
    except ValidationError as erro:
        messages.error(request, " ".join(erro.messages))
    return _responder_linha(request, consulta)


# ---------------- Nova consulta ----------------

@recepcao_required
def nova_consulta(request):
    if request.method == "POST":
        return _criar_consulta(request)

    hoje = timezone.localdate()
    paciente = Paciente.objects.filter(pk=_int(request.GET.get("paciente")), ativo=True).first()
    profissionais = _profissionais()
    profissional = profissionais.filter(pk=_int(request.GET.get("profissional"))).first()
    servicos = Servico.objects.none()
    servico = None
    if profissional:
        servicos = Servico.objects.filter(ativo=True, especialidade__in=profissional.especialidades.all())
        if profissional.servicos.exists():
            servicos = servicos.filter(pk__in=profissional.servicos.values("pk"))
        servicos = servicos.order_by("nome")
        servico = servicos.filter(pk=_int(request.GET.get("servico"))).first() or (
            servicos.first() if servicos.count() == 1 else None
        )
    data = max(_data(request.GET.get("data"), hoje), hoje)
    horarios = []
    if profissional and servico:
        horarios = horarios_livres(profissional, servico, data, respeitar_antecedencia=False)

    contexto = {
        "paciente": paciente,
        "profissionais": profissionais,
        "profissional": profissional,
        "servicos": servicos,
        "servico": servico,
        "data": data,
        "hoje": hoje,
        "horarios": horarios,
        "periodos": agenda_selectors._periodos(horarios) if horarios else [],
        "busca": request.GET.get("q", ""),
        "resultados": selectors.buscar_pacientes(request.GET.get("q")) if not paciente else [],
    }
    return render(request, "painel/nova_consulta.html", contexto)


def _criar_consulta(request):
    voltar = reverse("painel:nova_consulta") + "?" + request.POST.get("query", "")
    paciente = get_object_or_404(Paciente, pk=_int(request.POST.get("paciente")))
    profissional = get_object_or_404(Profissional, pk=_int(request.POST.get("profissional")))
    servico = get_object_or_404(Servico, pk=_int(request.POST.get("servico")))
    encaixe = request.POST.get("encaixe") == "on"
    data = _data(request.POST.get("data"))

    inicio = None
    texto = request.POST.get("hora_encaixe") if encaixe else request.POST.get("horario")
    if data and texto:
        try:
            hora = datetime.strptime(texto, "%H:%M").time()
            inicio = timezone.make_aware(datetime.combine(data, hora), timezone.get_current_timezone())
        except ValueError:
            inicio = None
    if inicio is None:
        messages.error(request, "Escolha um horário.")
        return redirect(voltar)

    try:
        consulta = consultas.agendar(
            paciente=paciente,
            profissional=profissional,
            servico=servico,
            inicio=inicio,
            usuario=request.user,
            origem=Consulta.Origem.RECEPCAO,
            encaixe=encaixe,
            observacao=request.POST.get("observacao", "").strip(),
        )
    except ValidationError as erro:
        messages.error(request, " ".join(erro.messages))
        return redirect(voltar)

    messages.success(
        request, f"Consulta de {paciente.nome} marcada para {timezone.localtime(inicio):%d/%m às %H:%M}."
    )
    return redirect(reverse("painel:agenda") + f"?data={data.isoformat()}")


# ---------------- Pacientes ----------------

@recepcao_required
def buscar_pacientes(request):
    resultados = selectors.buscar_pacientes(request.GET.get("q"))
    destino = request.GET.get("destino", "nova")
    return render(request, "painel/_resultados_pacientes.html", {"resultados": resultados, "destino": destino})


@recepcao_required
def pacientes(request):
    termo = request.GET.get("q", "").strip()
    lista = selectors.buscar_pacientes(termo, limite=200) if termo else Paciente.objects.filter(ativo=True).order_by("nome")
    pagina = Paginator(lista, 25).get_page(request.GET.get("pagina"))
    return render(request, "painel/pacientes.html", {"pagina": pagina, "termo": termo})


@recepcao_required
def paciente_form(request, pk=None):
    paciente = get_object_or_404(Paciente, pk=pk) if pk else None
    form = PacienteForm(request.POST or None, instance=paciente)
    if request.method == "POST" and form.is_valid():
        paciente = form.save()
        messages.success(request, f"Cadastro de {paciente.nome} salvo.")
        if request.POST.get("depois") == "agendar":
            return redirect(reverse("painel:nova_consulta") + f"?paciente={paciente.pk}")
        return redirect("painel:paciente", pk=paciente.pk)
    return render(request, "painel/paciente_form.html", {"form": form, "paciente": paciente,
                                                          "depois": request.GET.get("depois", "")})


@recepcao_required
def paciente_detalhe(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)
    historico = (
        paciente.consultas.select_related("profissional__usuario", "servico").order_by("-inicio")[:50]
    )
    return render(request, "painel/paciente_detalhe.html", {"paciente": paciente, "historico": historico})
