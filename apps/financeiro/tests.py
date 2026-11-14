from datetime import date, time, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.agenda.models import HorarioAtendimento
from apps.agenda.services import _aware
from apps.agendamentos import services as consultas
from apps.atendimentos.services import registrar_atendimento
from apps.clinica.models import Especialidade, Profissional, Servico
from apps.contas.models import Usuario
from apps.financeiro.selectors import resumo_mensal
from apps.financeiro.services import registrar_pagamento, total_pago
from apps.pacientes.models import Paciente


class FinanceiroTests(TestCase):
    def setUp(self):
        esp = Especialidade.objects.create(nome="Clínico geral")
        self.servico = Servico.objects.create(especialidade=esp, nome="Consulta", duracao_min=30, preco=Decimal("150"))
        user = Usuario.objects.create_user("medico@teste.com", "senha-forte-123", nome="Dr. Teste")
        self.prof = Profissional.objects.create(usuario=user, registro="1234")
        dia = timezone.localdate() + timedelta(days=2)
        HorarioAtendimento.objects.create(profissional=self.prof, dia_semana=dia.weekday(), hora_inicio=time(8), hora_fim=time(12))
        paciente = Paciente.objects.create(nome="Ana", cpf="52998224725", data_nascimento=date(1990, 1, 1), telefone="89999999999")
        self.consulta = consultas.agendar(paciente=paciente, profissional=self.prof, servico=self.servico, inicio=_aware(dia, time(8)))

    def test_atendimento_marca_consulta_realizada(self):
        registrar_atendimento(self.consulta, observacoes="Paciente bem.")
        self.consulta.refresh_from_db()
        self.assertEqual(self.consulta.status, "realizada")

    def test_pagamento_e_resumo(self):
        registrar_pagamento(self.consulta, valor=Decimal("150"), forma="pix")
        self.assertEqual(total_pago(self.consulta), Decimal("150"))
        hoje = timezone.localdate()
        resumo = resumo_mensal(hoje.year, hoje.month)
        self.assertEqual(resumo["receita_total"], Decimal("150"))
        self.assertEqual(resumo["receita_por_forma"][0]["forma"], "pix")

    def test_nao_paga_consulta_cancelada(self):
        consultas.cancelar(self.consulta, pela_recepcao=True)
        with self.assertRaises(ValidationError):
            registrar_pagamento(self.consulta, valor=Decimal("150"), forma="pix")
