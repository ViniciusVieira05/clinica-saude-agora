from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password

from apps.core.validators import somente_digitos, validar_cpf
from apps.pacientes.models import Paciente

from .models import Usuario


class EntrarForm(AuthenticationForm):
    username = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(attrs={"autofocus": True, "autocomplete": "email", "placeholder": "seu@email.com"}),
    )
    password = forms.CharField(
        label="Senha",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )
    error_messages = {
        "invalid_login": "E-mail ou senha incorretos.",
        "inactive": "Esta conta está desativada. Fale com a recepção.",
    }


class CriarContaForm(forms.Form):
    nome = forms.CharField(label="Nome completo", max_length=150,
                           widget=forms.TextInput(attrs={"autocomplete": "name"}))
    cpf = forms.CharField(label="CPF", max_length=14,
                          widget=forms.TextInput(attrs={"inputmode": "numeric", "placeholder": "000.000.000-00", "data-mascara": "cpf"}))
    data_nascimento = forms.DateField(label="Data de nascimento",
                                      widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))
    telefone = forms.CharField(label="Telefone / WhatsApp", max_length=20,
                               widget=forms.TextInput(attrs={"inputmode": "tel", "autocomplete": "tel", "placeholder": "(00) 00000-0000", "data-mascara": "telefone"}))
    email = forms.EmailField(label="E-mail", widget=forms.EmailInput(attrs={"autocomplete": "email"}))
    senha1 = forms.CharField(label="Senha", strip=False,
                             widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
                             help_text="Mínimo de 8 caracteres, sem ser só números.")
    senha2 = forms.CharField(label="Confirme a senha", strip=False,
                             widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
    aceite_termos = forms.BooleanField(
        label="Li e aceito a Política de Privacidade e os Termos de Uso.",
        error_messages={"required": "É preciso aceitar para criar a conta."},
    )

    def clean_cpf(self):
        cpf = somente_digitos(self.cleaned_data["cpf"])
        validar_cpf(cpf)
        if Paciente.objects.filter(cpf=cpf, usuario__isnull=False).exists():
            raise forms.ValidationError("Já existe uma conta com este CPF. Entre ou recupere a senha.")
        return cpf

    def clean_telefone(self):
        telefone = somente_digitos(self.cleaned_data["telefone"])
        if len(telefone) < 10:
            raise forms.ValidationError("Informe o telefone com DDD.")
        return telefone

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if Usuario.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Este e-mail já tem cadastro. Entre ou recupere a senha.")
        return email

    def clean(self):
        dados = super().clean()
        cpf, nascimento = dados.get("cpf"), dados.get("data_nascimento")
        if cpf and nascimento:
            ficha = Paciente.objects.filter(cpf=cpf, usuario__isnull=True).first()
            if ficha and ficha.data_nascimento != nascimento:
                # Proteção: só liga a conta à ficha da recepção se a data de nascimento conferir.
                self.add_error(
                    "cpf",
                    "Este CPF já está cadastrado na clínica com outros dados. "
                    "Fale com a recepção para liberar seu acesso.",
                )
        senha1, senha2 = dados.get("senha1"), dados.get("senha2")
        if senha1 and senha2 and senha1 != senha2:
            self.add_error("senha2", "As senhas não são iguais.")
        elif senha1:
            usuario_teste = Usuario(email=dados.get("email", ""), nome=dados.get("nome", ""))
            try:
                validate_password(senha1, user=usuario_teste)
            except forms.ValidationError as erro:
                self.add_error("senha1", erro)
        return dados


class MinhaContaForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = ["telefone", "cep", "endereco", "bairro", "cidade", "uf"]
        widgets = {
            "telefone": forms.TextInput(attrs={"inputmode": "tel", "data-mascara": "telefone"}),
            "cep": forms.TextInput(attrs={"inputmode": "numeric", "data-mascara": "cep", "data-viacep": "1", "placeholder": "00000-000"}),
        }