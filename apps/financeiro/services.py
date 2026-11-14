"""Registro de pagamentos."""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import Sum

from apps.agendamentos.models import Consulta

from .models import Pagamento


def total_pago(consulta):
    return consulta.pagamentos.filter(ativo=True).aggregate(t=Sum("valor"))["t"] or Decimal("0")


def registrar_pagamento(consulta, *, valor, forma, usuario=None, observacao=""):
    if consulta.status == Consulta.Status.CANCELADA:
        raise ValidationError("Não é possível registrar pagamento de consulta cancelada.")
    if valor <= 0:
        raise ValidationError("O valor precisa ser maior que zero.")
    pagamento = Pagamento(
        consulta=consulta, valor=valor, forma=forma, registrado_por=usuario, observacao=observacao
    )
    pagamento.full_clean()
    pagamento.save()
    return pagamento
