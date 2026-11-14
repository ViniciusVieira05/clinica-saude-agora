"""Consultas do relatório financeiro (RF18)."""
from datetime import date, datetime

from django.db.models import Count, Q, Sum
from django.utils import timezone

from apps.agendamentos.models import Consulta

from .models import Pagamento


def _periodo(ano, mes):
    inicio = timezone.make_aware(datetime(ano, mes, 1))
    fim_ano, fim_mes = (ano + 1, 1) if mes == 12 else (ano, mes + 1)
    fim = timezone.make_aware(datetime(fim_ano, fim_mes, 1))
    return inicio, fim


def resumo_mensal(ano, mes):
    """Totais do mês: receita, consultas por status e receita por profissional e por forma."""
    inicio, fim = _periodo(ano, mes)

    pagamentos = Pagamento.objects.filter(ativo=True, pago_em__gte=inicio, pago_em__lt=fim)
    consultas = Consulta.objects.filter(inicio__gte=inicio, inicio__lt=fim)

    por_status = dict(consultas.values_list("status").annotate(n=Count("id")))
    return {
        "periodo": date(ano, mes, 1),
        "receita_total": pagamentos.aggregate(t=Sum("valor"))["t"] or 0,
        "consultas_total": consultas.exclude(status=Consulta.Status.CANCELADA).count(),
        "realizadas": por_status.get(Consulta.Status.REALIZADA, 0),
        "faltas": por_status.get(Consulta.Status.FALTOU, 0),
        "canceladas": por_status.get(Consulta.Status.CANCELADA, 0),
        "receita_por_profissional": list(
            pagamentos.values("consulta__profissional__usuario__nome")
            .annotate(total=Sum("valor"), quantidade=Count("id"))
            .order_by("-total")
        ),
        "receita_por_forma": list(
            pagamentos.values("forma").annotate(total=Sum("valor")).order_by("-total")
        ),
    }
