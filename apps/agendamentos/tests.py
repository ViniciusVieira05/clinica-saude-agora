from datetime import date, time, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.agenda.models import Bloqueio, HorarioAtendimento
from apps.agenda.services import horarios_livres, _aware
from apps.agendamentos import services
from apps.agendamentos.models import Consulta
from apps.clinica.models import Especialidade, Profissional, Servico
from apps.contas.models import Usuario
from apps.pacientes.models import Paciente


def proxima(dia_semana):
    """Próxima data (a partir de amanhã + 1) que cai no dia da semana pedido."""
    d = timezone.localdate() + timedelta(days=2)
    while d.weekday() != dia_semana:
        d += timedelta(days=1)
    return d


@override_settings(AGENDAMENTO_ANTECEDENCIA_MIN_HORAS=2, AGENDAMENTO_LIMITE_DIAS=60, CANCELAMENTO_PRAZO_HORAS=12)
class AgendamentoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        esp = Especialidade.objects.create(nome="Clínico geral")
        cls.servico = Servico.objects.create(especialidade=esp, nome="Consulta", duracao_min=30, preco=Decimal("150"))
        user = Usuario.objects.create_user("medico@teste.com", "senha-forte-123", nome="Dr. Teste", tipo="profissional")
        cls.prof = Profissional.objects.create(usuario=user, registro="1234")
        cls.prof.especialidades.add(esp)
        HorarioAtendimento.objects.create(
            profissional=cls.prof, dia_semana=0, hora_inicio=time(8), hora_fim=time(12),
            intervalo_inicio=time(10), intervalo_fim=time(10, 30),
        )
        cls.p1 = Paciente.objects.create(nome="Ana", cpf="52998224725", data_nascimento=date(1990, 1, 1), telefone="89999999999")
        cls.p2 = Paciente.objects.create(nome="Bruno", cpf="11144477735", data_nascimento=date(1985, 5, 5), telefone="89988888888")
        cls.segunda = proxima(0)

    def test_gera_horarios_sem_o_intervalo(self):
        livres = [timezone.localtime(h).strftime("%H:%M") for h in horarios_livres(self.prof, self.servico, self.segunda)]
        self.assertEqual(livres, ["08:00", "08:30", "09:00", "09:30", "10:30", "11:00", "11:30"])

    def test_dia_sem_expediente_nao_tem_horarios(self):
        self.assertEqual(horarios_livres(self.prof, self.servico, proxima(2)), [])

    def test_consulta_ocupa_o_horario(self):
        inicio = _aware(self.segunda, time(9))
        services.agendar(paciente=self.p1, profissional=self.prof, servico=self.servico, inicio=inicio)
        self.assertNotIn(inicio, horarios_livres(self.prof, self.servico, self.segunda))

    def test_bloqueio_da_clinica_remove_horarios(self):
        Bloqueio.objects.create(inicio=_aware(self.segunda, time(8)), fim=_aware(self.segunda, time(12)), motivo="Feriado")
        self.assertEqual(horarios_livres(self.prof, self.servico, self.segunda), [])

    def test_nao_agenda_horario_ocupado(self):
        inicio = _aware(self.segunda, time(9))
        services.agendar(paciente=self.p1, profissional=self.prof, servico=self.servico, inicio=inicio)
        with self.assertRaises(ValidationError):
            services.agendar(paciente=self.p2, profissional=self.prof, servico=self.servico, inicio=inicio)

    def test_banco_impede_sobreposicao_mesmo_no_encaixe(self):
        inicio = _aware(self.segunda, time(9))
        services.agendar(paciente=self.p1, profissional=self.prof, servico=self.servico, inicio=inicio)
        with self.assertRaises(ValidationError):
            services.agendar(
                paciente=self.p2, profissional=self.prof, servico=self.servico,
                inicio=inicio + timedelta(minutes=15), encaixe=True, origem=Consulta.Origem.RECEPCAO,
            )

    def test_cancelada_libera_o_horario(self):
        inicio = _aware(self.segunda, time(9))
        consulta = services.agendar(paciente=self.p1, profissional=self.prof, servico=self.servico, inicio=inicio)
        services.cancelar(consulta)
        self.assertIn(inicio, horarios_livres(self.prof, self.servico, self.segunda))

    def test_preco_copiado_do_servico(self):
        consulta = services.agendar(
            paciente=self.p1, profissional=self.prof, servico=self.servico, inicio=_aware(self.segunda, time(8))
        )
        self.servico.preco = Decimal("200")
        self.servico.save()
        consulta.refresh_from_db()
        self.assertEqual(consulta.preco, Decimal("150"))
