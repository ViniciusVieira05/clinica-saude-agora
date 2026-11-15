from datetime import date, time, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
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


class TelaAgendamentoTests(TestCase):
    """Fluxo do paciente no site."""

    @classmethod
    def setUpTestData(cls):
        esp = Especialidade.objects.create(nome="Clínico geral")
        cls.esp = esp
        cls.servico = Servico.objects.create(especialidade=esp, nome="Consulta", duracao_min=30, preco=Decimal("150"))
        medico = Usuario.objects.create_user("medico2@teste.com", "senha-forte-123", nome="Dra. Lia", tipo="profissional")
        cls.prof = Profissional.objects.create(usuario=medico, registro="999")
        cls.prof.especialidades.add(esp)
        cls.dia = timezone.localdate() + timedelta(days=3)
        HorarioAtendimento.objects.create(profissional=cls.prof, dia_semana=cls.dia.weekday(), hora_inicio=time(8), hora_fim=time(10))
        cls.usuario = Usuario.objects.create_user("paciente@teste.com", "Senha-forte-2026", nome="Rui Alves")
        Paciente.objects.create(usuario=cls.usuario, nome="Rui Alves", cpf="52998224725", data_nascimento=date(1990, 1, 1), telefone="89999999999")

    def escolha(self, hora="09:00"):
        return f"{self.prof.pk}|{self.servico.pk}|{self.dia.isoformat()}T{hora}"

    def test_mostra_profissional_e_horarios(self):
        resposta = self.client.get(reverse("agendamentos:agendar"))
        self.assertContains(resposta, "Dra. Lia")
        self.assertContains(resposta, "Clínico geral")
        self.assertContains(resposta, "08:30")

    def test_filtra_por_especialidade(self):
        outra = Especialidade.objects.create(nome="Pediatria")
        resposta = self.client.get(reverse("agendamentos:agendar"), {"especialidade": outra.pk})
        self.assertContains(resposta, "Dra. Lia")  # filtro inválido (sem agenda) é ignorado

    def test_sem_login_vai_para_o_login_guardando_a_escolha(self):
        resposta = self.client.post(reverse("agendamentos:confirmar"), {"escolha": self.escolha()})
        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(resposta.url.startswith(reverse("contas:entrar")))
        self.assertIn("escolha", resposta.url)
        self.assertFalse(Consulta.objects.exists())

    def test_confirmar_cria_consulta(self):
        self.client.force_login(self.usuario)
        resposta = self.client.post(reverse("agendamentos:confirmar"), {"escolha": self.escolha()})
        consulta = Consulta.objects.get()
        self.assertRedirects(resposta, reverse("agendamentos:confirmado", args=[consulta.pk]))
        self.assertEqual(consulta.origem, "site")
        self.assertEqual(consulta.paciente.usuario, self.usuario)

    def test_confirmacao_tem_botao_do_whatsapp(self):
        self.client.force_login(self.usuario)
        self.client.post(reverse("agendamentos:confirmar"), {"escolha": self.escolha()})
        resposta = self.client.get(reverse("agendamentos:confirmado", args=[Consulta.objects.get().pk]))
        self.assertContains(resposta, "wa.me/")
        self.assertContains(resposta, "Rui%20Alves")

    def test_horario_ocupado_volta_com_erro(self):
        self.client.force_login(self.usuario)
        self.client.post(reverse("agendamentos:confirmar"), {"escolha": self.escolha()})
        resposta = self.client.post(reverse("agendamentos:confirmar"), {"escolha": self.escolha()}, follow=True)
        self.assertEqual(Consulta.objects.count(), 1)
        self.assertContains(resposta, "não está disponível")

    def test_outro_paciente_nao_ve_a_confirmacao(self):
        self.client.force_login(self.usuario)
        self.client.post(reverse("agendamentos:confirmar"), {"escolha": self.escolha()})
        outro = Usuario.objects.create_user("outro@teste.com", "Senha-forte-2026", nome="Outro")
        self.client.force_login(outro)
        resposta = self.client.get(reverse("agendamentos:confirmado", args=[Consulta.objects.get().pk]))
        self.assertEqual(resposta.status_code, 404)


class MeusAgendamentosTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        esp = Especialidade.objects.create(nome="Clínico geral")
        cls.servico = Servico.objects.create(especialidade=esp, nome="Consulta", duracao_min=30, preco=Decimal("150"))
        medico = Usuario.objects.create_user("medico3@teste.com", "senha-forte-123", nome="Dr. Paulo", tipo="profissional")
        cls.prof = Profissional.objects.create(usuario=medico, registro="777")
        cls.prof.especialidades.add(esp)
        cls.dia = timezone.localdate() + timedelta(days=3)
        HorarioAtendimento.objects.create(profissional=cls.prof, dia_semana=cls.dia.weekday(), hora_inicio=time(8), hora_fim=time(12))
        cls.usuario = Usuario.objects.create_user("bia@teste.com", "Senha-forte-2026", nome="Bia Lopes")
        cls.paciente = Paciente.objects.create(usuario=cls.usuario, nome="Bia Lopes", cpf="52998224725", data_nascimento=date(1990, 1, 1), telefone="89999999999")

    def setUp(self):
        self.consulta = services.agendar(paciente=self.paciente, profissional=self.prof, servico=self.servico, inicio=_aware(self.dia, time(9)))
        self.client.force_login(self.usuario)

    def test_lista_proximas(self):
        resposta = self.client.get(reverse("agendamentos:meus"))
        self.assertContains(resposta, "Dr. Paulo")
        self.assertContains(resposta, "Remarcar")

    def test_cancelar(self):
        self.client.post(reverse("agendamentos:cancelar", args=[self.consulta.pk]))
        self.consulta.refresh_from_db()
        self.assertEqual(self.consulta.status, "cancelada")

    def test_nao_cancela_consulta_de_outro_paciente(self):
        outro = Usuario.objects.create_user("x@teste.com", "Senha-forte-2026", nome="X")
        self.client.force_login(outro)
        resposta = self.client.post(reverse("agendamentos:cancelar", args=[self.consulta.pk]))
        self.assertEqual(resposta.status_code, 404)

    @override_settings(CANCELAMENTO_PRAZO_HORAS=24 * 10)
    def test_fora_do_prazo_nao_cancela(self):
        self.client.post(reverse("agendamentos:cancelar", args=[self.consulta.pk]))
        self.consulta.refresh_from_db()
        self.assertEqual(self.consulta.status, "agendada")

    def test_remarcar(self):
        novo = f"{self.prof.pk}|{self.servico.pk}|{self.dia.isoformat()}T10:30"
        resposta = self.client.post(reverse("agendamentos:remarcar", args=[self.consulta.pk]), {"escolha": novo})
        self.assertRedirects(resposta, reverse("agendamentos:meus"))
        self.consulta.refresh_from_db()
        self.assertEqual(timezone.localtime(self.consulta.inicio).strftime("%H:%M"), "10:30")
