from django.conf import settings
from django.db import models

from apps.core.models import ModeloBase
from apps.core.validators import somente_digitos, validar_cpf


class Paciente(ModeloBase):
    class Sexo(models.TextChoices):
        FEMININO = "F", "Feminino"
        MASCULINO = "M", "Masculino"
        OUTRO = "O", "Outro"
        NAO_INFORMADO = "N", "Prefiro não informar"

    # Opcional: pacientes cadastrados pela recepção podem não ter login.
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="paciente",
        verbose_name="usuário",
    )
    nome = models.CharField("nome completo", max_length=150)
    cpf = models.CharField("CPF", max_length=14, unique=True, validators=[validar_cpf])
    data_nascimento = models.DateField("data de nascimento")
    sexo = models.CharField("sexo", max_length=1, choices=Sexo.choices, default=Sexo.NAO_INFORMADO)
    telefone = models.CharField("telefone / WhatsApp", max_length=20)
    email = models.EmailField("e-mail", blank=True)

    cep = models.CharField("CEP", max_length=9, blank=True)
    endereco = models.CharField("endereço", max_length=200, blank=True)
    bairro = models.CharField("bairro", max_length=100, blank=True)
    cidade = models.CharField("cidade", max_length=100, blank=True)
    uf = models.CharField("UF", max_length=2, blank=True)

    observacoes = models.TextField("observações da recepção", blank=True)
    aceite_termos_em = models.DateTimeField("aceitou os termos em", null=True, blank=True)

    class Meta:
        verbose_name = "paciente"
        verbose_name_plural = "pacientes"
        ordering = ["nome"]
        indexes = [
            models.Index(fields=["nome"]),
            models.Index(fields=["telefone"]),
        ]

    def save(self, *args, **kwargs):
        # Guarda CPF, telefone e CEP só com números.
        self.cpf = somente_digitos(self.cpf)
        self.telefone = somente_digitos(self.telefone)
        self.cep = somente_digitos(self.cep)
        super().save(*args, **kwargs)

    @property
    def cpf_formatado(self):
        c = self.cpf
        return f"{c[:3]}.{c[3:6]}.{c[6:9]}-{c[9:]}" if len(c) == 11 else c

    def __str__(self):
        return self.nome
