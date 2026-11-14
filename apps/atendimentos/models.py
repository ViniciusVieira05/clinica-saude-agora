from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.agendamentos.models import Consulta
from apps.core.models import ModeloBase


class Atendimento(ModeloBase):
    """Registro simples do que aconteceu na consulta (não é prontuário eletrônico)."""

    consulta = models.OneToOneField(
        Consulta, on_delete=models.PROTECT, related_name="atendimento", verbose_name="consulta"
    )
    observacoes = models.TextField("observações do atendimento", blank=True)
    retorno_sugerido_em = models.DateField("retorno sugerido para", null=True, blank=True)
    realizado_em = models.DateTimeField("realizado em", default=timezone.now)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="atendimentos_registrados",
        verbose_name="registrado por",
    )

    class Meta:
        verbose_name = "atendimento"
        verbose_name_plural = "atendimentos"
        ordering = ["-realizado_em"]

    def __str__(self):
        return f"Atendimento de {self.consulta.paciente} em {self.realizado_em:%d/%m/%Y}"
