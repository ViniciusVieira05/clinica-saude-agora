from decimal import Decimal

from django.db.models import Q, Sum
from django.utils import timezone

from apps.agendamentos.models import Consulta
from apps.core.validators import somente_digitos
from apps.financeiro.models import Pagamento
from apps.pacientes.models import Paciente


def consultas_do_dia(data, profissional=None):
    consultas = (
        Consulta.objects.filter(inicio__date=data)
        .select_related("paciente", "profissional__usuario", "servico")
        .prefetch_related("pagamentos")
        .order_by("inicio")
    )
    if profissional is not None:
        consultas = consultas.filter(profissional=profissional)
    return consultas


def anotar_pagamento(consultas):
    for c in consultas:
        c.total_pago = sum((p.valor for p in c.pagamentos.all() if p.ativo), Decimal("0"))
        c.esta_paga = c.total_pago >= c.preco
    return consultas


def resumo_do_dia(consultas):
    lista = list(consultas)
    ativas = [c for c in lista if c.status != Consulta.Status.CANCELADA]
    return {
        "total": len(ativas),
        "confirmadas": sum(1 for c in ativas if c.status == Consulta.Status.CONFIRMADA),
        "realizadas": sum(1 for c in ativas if c.status == Consulta.Status.REALIZADA),
        "faltas": sum(1 for c in ativas if c.status == Consulta.Status.FALTOU),
        "recebido": Pagamento.objects.filter(consulta__in=lista, ativo=True).aggregate(t=Sum("valor"))["t"] or 0,
    }


def buscar_pacientes(termo, limite=8):
    termo = (termo or "").strip()
    if len(termo) < 2:
        return Paciente.objects.none()
    digitos = somente_digitos(termo)
    filtro = Q(nome__icontains=termo)
    if len(digitos) >= 3:
        filtro |= Q(cpf__startswith=digitos) | Q(telefone__contains=digitos)
    return Paciente.objects.filter(filtro, ativo=True).order_by("nome")[:limite]
