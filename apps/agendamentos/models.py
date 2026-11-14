from django.conf import settings
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateTimeRangeField, RangeBoundary, RangeOperators
from django.db import models
from django.db.models import F, Func, Q

from apps.clinica.models import Profissional, Servico
from apps.core.models import ModeloBase
from apps.pacientes.models import Paciente


class TsTzRange(Func):
    """Monta um intervalo de tempo [inicio, fim) no PostgreSQL."""

    function = "TSTZRANGE"
    output_field = DateTimeRangeField()


class Consulta(ModeloBase):
    class Status(models.TextChoices):
        AGENDADA = "agendada", "Agendada"
        CONFIRMADA = "confirmada", "Confirmada"
        REALIZADA = "realizada", "Realizada"
        CANCELADA = "cancelada", "Cancelada"
        FALTOU = "faltou", "Faltou"

    class Origem(models.TextChoices):
        SITE = "site", "Site"
        RECEPCAO = "recepcao", "Recepção"

    paciente = models.ForeignKey(
        Paciente, on_delete=models.PROTECT, related_name="consultas", verbose_name="paciente"
    )
    profissional = models.ForeignKey(
        Profissional, on_delete=models.PROTECT, related_name="consultas", verbose_name="profissional"
    )
    servico = models.ForeignKey(
        Servico, on_delete=models.PROTECT, related_name="consultas", verbose_name="serviço"
    )
    inicio = models.DateTimeField("início")
    fim = models.DateTimeField("fim")
    status = models.CharField("status", max_length=12, choices=Status.choices, default=Status.AGENDADA)
    preco = models.DecimalField("preço (R$)", max_digits=8, decimal_places=2)
    origem = models.CharField("origem", max_length=10, choices=Origem.choices, default=Origem.SITE)
    encaixe = models.BooleanField("encaixe", default=False)
    observacao = models.TextField("observação", blank=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="consultas_criadas",
        verbose_name="criado por",
    )
    cancelada_em = models.DateTimeField("cancelada em", null=True, blank=True)

    class Meta:
        verbose_name = "consulta"
        verbose_name_plural = "consultas"
        ordering = ["inicio"]
        indexes = [
            models.Index(fields=["profissional", "inicio"]),
            models.Index(fields=["paciente", "inicio"]),
            models.Index(fields=["status"]),
        ]
        constraints = [
            models.CheckConstraint(condition=Q(inicio__lt=F("fim")), name="consulta_inicio_antes_do_fim"),
            # RN03: o mesmo profissional nunca tem duas consultas sobrepostas.
            ExclusionConstraint(
                name="consulta_sem_sobreposicao_profissional",
                expressions=[
                    (TsTzRange("inicio", "fim", RangeBoundary()), RangeOperators.OVERLAPS),
                    ("profissional", RangeOperators.EQUAL),
                ],
                condition=~Q(status="cancelada"),
                violation_error_message="Esse horário já está ocupado para este profissional.",
            ),
            # RN07: o mesmo paciente nunca tem duas consultas sobrepostas.
            ExclusionConstraint(
                name="consulta_sem_sobreposicao_paciente",
                expressions=[
                    (TsTzRange("inicio", "fim", RangeBoundary()), RangeOperators.OVERLAPS),
                    ("paciente", RangeOperators.EQUAL),
                ],
                condition=~Q(status="cancelada"),
                violation_error_message="O paciente já tem uma consulta nesse horário.",
            ),
        ]

    def __str__(self):
        return f"{self.paciente} com {self.profissional.nome} em {self.inicio:%d/%m/%Y %H:%M}"
