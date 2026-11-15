from datetime import datetime
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.clinica.models import Profissional, Servico

from . import selectors, services
from .models import Consulta


def _int(valor):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def _data(valor):
    try:
        return datetime.strptime(valor, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def _horario(valor):
    try:
        return timezone.make_aware(datetime.strptime(valor, "%Y-%m-%dT%H:%M"), timezone.get_current_timezone())
    except (TypeError, ValueError):
        return None


def _ler_escolha(valor):
    """Escolha vem como 'profissional|serviço|AAAA-MM-DDTHH:MM'."""
    try:
        prof, serv, quando = (valor or "").split("|")
    except ValueError:
        return None
    inicio = _horario(quando)
    if not (_int(prof) and _int(serv) and inicio):
        return None
    return {"profissional": _int(prof), "servico": _int(serv), "inicio": inicio, "valor": valor}


def _filtros(params):
    """Parâmetros de filtro que devem ser mantidos ao voltar para a tela."""
    return {k: params[k] for k in ("especialidade", "servico") if params.get(k)}


def agendar(request):
    especialidades = selectors.especialidades_agendaveis()
    especialidade = especialidades.filter(pk=_int(request.GET.get("especialidade"))).first()
    servicos = selectors.servicos_da_especialidade(especialidade) if especialidade else []
    servico = servicos.filter(pk=_int(request.GET.get("servico"))).first() if especialidade else None

    escolha = _ler_escolha(request.GET.get("escolha"))
    contexto = {
        "especialidades": especialidades,
        "especialidade": especialidade,
        "servicos": servicos,
        "servico": servico,
        "linhas": selectors.agenda_dos_profissionais(especialidade, servico),
        "escolha": escolha["valor"] if escolha else "",
    }
    return render(request, "agendamentos/agendar.html", contexto)


@require_POST
def confirmar(request):
    filtros = _filtros(request.POST)
    voltar = reverse("agendamentos:agendar") + ("?" + urlencode(filtros) if filtros else "")
    escolha = _ler_escolha(request.POST.get("escolha"))
    if escolha is None:
        messages.error(request, "Escolha um horário para continuar.")
        return redirect(voltar)

    if not request.user.is_authenticated:
        # Guarda a escolha e manda para o login; depois volta para a mesma tela já marcada.
        destino = reverse("agendamentos:agendar") + "?" + urlencode({**filtros, "escolha": escolha["valor"]})
        messages.info(request, "Entre ou crie sua conta para confirmar o horário.")
        return redirect(reverse("contas:entrar") + "?" + urlencode({"next": destino}))

    paciente = getattr(request.user, "paciente", None)
    if paciente is None:
        messages.error(request, "Sua conta não tem ficha de paciente. Fale com a recepção.")
        return redirect(voltar)

    profissional = get_object_or_404(Profissional, pk=escolha["profissional"], ativo=True)
    servico = get_object_or_404(Servico, pk=escolha["servico"], ativo=True)
    try:
        consulta = services.agendar(
            paciente=paciente,
            profissional=profissional,
            servico=servico,
            inicio=escolha["inicio"],
            usuario=request.user,
            origem=Consulta.Origem.SITE,
        )
    except ValidationError as erro:
        messages.error(request, " ".join(erro.messages))
        return redirect(voltar)

    _enviar_email(request, consulta)
    return redirect("agendamentos:confirmado", pk=consulta.pk)


def _enviar_email(request, consulta):
    """E-mail é um extra; a confirmação principal é pelo WhatsApp."""
    email = consulta.paciente.email or request.user.email
    if not email:
        return
    texto = render_to_string("agendamentos/email_confirmacao.txt", {"consulta": consulta}, request=request)
    send_mail(
        subject=f"Consulta agendada para {timezone.localtime(consulta.inicio):%d/%m às %H:%M}",
        message=texto,
        from_email=None,
        recipient_list=[email],
        fail_silently=True,
    )


@login_required
def confirmado(request, pk):
    consulta = get_object_or_404(
        Consulta.objects.select_related("profissional__usuario", "servico__especialidade", "paciente"),
        pk=pk,
        paciente__usuario=request.user,
    )
    mensagem_whatsapp = render_to_string(
        "agendamentos/whatsapp_confirmacao.txt", {"consulta": consulta}, request=request
    ).strip()
    contexto = {
        "consulta": consulta,
        "prazo_cancelamento": settings.CANCELAMENTO_PRAZO_HORAS,
        "mensagem_whatsapp": mensagem_whatsapp,
    }
    return render(request, "agendamentos/confirmado.html", contexto)


def _consulta_do_usuario(request, pk):
    return get_object_or_404(
        Consulta.objects.select_related("profissional__usuario", "servico__especialidade", "paciente"),
        pk=pk,
        paciente__usuario=request.user,
    )


@login_required
def meus_agendamentos(request):
    agora = timezone.now()
    consultas = (
        Consulta.objects.filter(paciente__usuario=request.user)
        .select_related("profissional__usuario", "servico__especialidade", "paciente")
    )
    proximas = list(
        consultas.filter(
            fim__gte=agora, status__in=[Consulta.Status.AGENDADA, Consulta.Status.CONFIRMADA]
        ).order_by("inicio")
    )
    for consulta in proximas:
        consulta.pode_alterar = services.pode_alterar_pelo_site(consulta)
        consulta.mensagem_whatsapp = (
            f"Olá! Sou {consulta.paciente.nome}. Sobre meu agendamento nº {consulta.pk} "
            f"({timezone.localtime(consulta.inicio):%d/%m às %H:%M} com {consulta.profissional.nome}): "
        )
    historico = consultas.exclude(pk__in=[c.pk for c in proximas]).order_by("-inicio")[:20]
    contexto = {
        "proximas": proximas,
        "historico": historico,
        "prazo_cancelamento": settings.CANCELAMENTO_PRAZO_HORAS,
    }
    return render(request, "agendamentos/meus_agendamentos.html", contexto)


@require_POST
@login_required
def cancelar(request, pk):
    consulta = _consulta_do_usuario(request, pk)
    try:
        services.cancelar(consulta, pela_recepcao=False)
    except ValidationError as erro:
        messages.error(request, " ".join(erro.messages))
    else:
        messages.success(request, f"Consulta de {timezone.localtime(consulta.inicio):%d/%m às %H:%M} cancelada.")
    return redirect("agendamentos:meus")


@login_required
def remarcar(request, pk):
    consulta = _consulta_do_usuario(request, pk)
    if not services.pode_alterar_pelo_site(consulta):
        messages.error(
            request,
            f"Essa consulta só pode ser remarcada pela recepção (prazo de {settings.CANCELAMENTO_PRAZO_HORAS} horas).",
        )
        return redirect("agendamentos:meus")

    if request.method == "POST":
        escolha = _ler_escolha(request.POST.get("escolha"))
        if (
            escolha is None
            or escolha["profissional"] != consulta.profissional_id
            or escolha["servico"] != consulta.servico_id
        ):
            messages.error(request, "Escolha um novo horário.")
            return redirect("agendamentos:remarcar", pk=consulta.pk)
        antes = timezone.localtime(consulta.inicio)
        try:
            services.remarcar(consulta, escolha["inicio"], pela_recepcao=False)
        except ValidationError as erro:
            messages.error(request, " ".join(erro.messages))
            return redirect("agendamentos:remarcar", pk=consulta.pk)
        messages.success(
            request,
            f"Remarcado: de {antes:%d/%m %H:%M} para {timezone.localtime(consulta.inicio):%d/%m às %H:%M}.",
        )
        return redirect("agendamentos:meus")

    linha = {
        "profissional": consulta.profissional,
        "servico": consulta.servico,
        "dias": selectors.proximos_dias(consulta.profissional, consulta.servico),
    }
    return render(request, "agendamentos/remarcar.html", {"consulta": consulta, "linha": linha})
