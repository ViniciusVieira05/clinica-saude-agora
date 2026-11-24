from django.contrib import messages
from django.contrib.auth import login, views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme

from . import services
from .forms import CriarContaForm, EntrarForm, MinhaContaForm


def _destino(request):
    proximo = request.POST.get("next") or request.GET.get("next")
    if proximo and url_has_allowed_host_and_scheme(proximo, allowed_hosts={request.get_host()}):
        return proximo
    return reverse_lazy("contas:minha_area")


class EntrarView(auth_views.LoginView):
    template_name = "contas/entrar.html"
    authentication_form = EntrarForm
    redirect_authenticated_user = True

    def get_default_redirect_url(self):
        from apps.painel.permissoes import eh_recepcao

        if eh_recepcao(self.request.user):
            return reverse_lazy("painel:agenda")
        if hasattr(self.request.user, "paciente"):
            return reverse_lazy("contas:minha_area")
        return super().get_default_redirect_url()


class SairView(auth_views.LogoutView):
    pass


def criar_conta(request):
    if request.user.is_authenticated:
        return redirect(_destino(request))
    form = CriarContaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        dados = form.cleaned_data
        usuario = services.criar_conta_paciente(
            nome=dados["nome"],
            cpf=dados["cpf"],
            data_nascimento=dados["data_nascimento"],
            telefone=dados["telefone"],
            email=dados["email"],
            senha=dados["senha1"],
        )
        login(request, usuario)
        messages.success(request, f"Pronto, {usuario.nome.split()[0]}. Sua conta foi criada.")
        return redirect(_destino(request))
    return render(request, "contas/criar.html", {"form": form, "next": request.GET.get("next", "")})


@login_required
def minha_conta(request):
    paciente = getattr(request.user, "paciente", None)
    if paciente is None:
        messages.info(request, "Sua conta não tem ficha de paciente.")
        return redirect("site_publico:inicio")
    form = MinhaContaForm(request.POST or None, instance=paciente)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Dados atualizados.")
        return redirect("contas:minha_conta")
    return render(request, "contas/minha_conta.html", {"form": form, "paciente": paciente})


class EsqueciSenhaView(auth_views.PasswordResetView):
    template_name = "contas/senha_esqueci.html"
    email_template_name = "contas/email_senha.txt"
    subject_template_name = "contas/email_senha_assunto.txt"
    success_url = reverse_lazy("contas:senha_enviada")


class SenhaEnviadaView(auth_views.PasswordResetDoneView):
    template_name = "contas/senha_enviada.html"


class NovaSenhaView(auth_views.PasswordResetConfirmView):
    template_name = "contas/senha_nova.html"
    success_url = reverse_lazy("contas:senha_concluida")


class SenhaConcluidaView(auth_views.PasswordResetCompleteView):
    template_name = "contas/senha_concluida.html"

@login_required
def minha_area(request):
    from django.utils import timezone

    from apps.agendamentos import services as consultas
    from apps.agendamentos.models import Consulta

    paciente = getattr(request.user, "paciente", None)
    if paciente is None:
        return redirect("site_publico:inicio")
    agora = timezone.now()
    base = paciente.consultas.select_related("profissional__usuario", "servico__especialidade")
    proximas = list(
        base.filter(fim__gte=agora, status__in=[Consulta.Status.AGENDADA, Consulta.Status.CONFIRMADA]).order_by("inicio")[:4]
    )
    proxima = proximas[0] if proximas else None
    if proxima:
        proxima.pode_alterar = consultas.pode_alterar_pelo_site(proxima)
    ultimas = base.filter(inicio__lt=agora).order_by("-inicio")[:5]
    contexto = {
        "paciente": paciente,
        "proxima": proxima,
        "outras": proximas[1:],
        "ultimas": ultimas,
        "primeiro_nome": paciente.nome.split()[0],
    }
    return render(request, "contas/minha_area.html", contexto)
