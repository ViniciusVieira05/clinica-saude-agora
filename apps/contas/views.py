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
    return reverse_lazy("site_publico:inicio")


class EntrarView(auth_views.LoginView):
    template_name = "contas/entrar.html"
    authentication_form = EntrarForm
    redirect_authenticated_user = True


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