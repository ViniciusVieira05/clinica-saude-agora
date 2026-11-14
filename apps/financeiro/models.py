from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.agendamentos.models import Consulta
from apps.core.models import ModeloBase


class Pagamento(ModeloBase):
    class Forma(models.TextChoices):
        PIX = "pix", "Pix"
        DINHEIRO = "dinheiro", "Dinheiro"
        DEBITO = "debito", "Cartão de débito"
        CREDITO = "credito", "Cartão de crédito"

    consulta = models.ForeignKey(
        Consulta, on_delete=models.PROTECT, related_name="pagamentos", verbose_name="consulta"
    )
    valor = models.DecimalField("valor (R$)", max_digits=8, decimal_places=2)
    forma = models.CharField("forma de pagamento", max_length=10, choices=Forma.choices)
    pago_em = models.DateTimeField("pago em", default=timezone.now)
    observacao = models.CharField("observação", max_length=200, blank=True)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pagamentos_registrados",
        verbose_name="registrado por",
    )

    class Meta:
        verbose_name = "pagamento"
        verbose_name_plural = "pagamentos"
        ordering = ["-pago_em"]
        indexes = [models.Index(fields=["pago_em"])]
        constraints = [
            models.CheckConstraint(condition=Q(valor__gt=0), name="pagamento_valor_positivo"),
        ]

    def __str__(self):
        return f"R$ {self.valor} ({self.get_forma_display()}) – {self.consulta.paciente}"
