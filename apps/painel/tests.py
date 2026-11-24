from datetime import date, time, timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.agenda.models import HorarioAtendimento
from apps.agenda.services import _aware
from apps.agendamentos import services
from apps.agendamentos.models import Consulta
from apps.clinica.models import Especialidade, Profissional, Servico
from apps.contas.models import Usuario
from apps.pacientes.models import Paciente


class PainelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        esp = Especialidade.objects.create(nome="Clínico geral")
        cls.servico = Servico.objects.create(especialidade=esp, nome="Consulta", duracao_min=30, preco=Decimal("150"))
        medico = Usuario.objects.create_user("med@teste.com", "senha-forte-123", nome="Dr. Caio", tipo="profissional")
        cls.prof = Profissional.objects.create(usuario=medico, registro="555")
        cls.prof.especialidades.add(esp)
        cls.dia = timezone.localdate() + timedelta(days=2)
        HorarioAtendimento.objects.create(profissional=cls.prof, dia_semana=cls.dia.weekday(), hora_inicio=time(8), hora_fim=time(12))
        cls.recepcao = Usuario.objects.create_user("rec@teste.com", "Senha-forte-2026", nome="Lia Recepção", tipo="recepcao")
        cls.paciente = Paciente.objects.create(nome="João Melo", cpf="52998224725", data_nascimento=date(1980, 5, 5), telefone="89999990000")

    def setUp(self):
        self.client.force_login(self.recepcao)

    def test_paciente_nao_entra_no_painel(self):
        comum = Usuario.objects.create_user("p@teste.com", "Senha-forte-2026", nome="Comum")
        self.client.force_login(comum)
        self.assertEqual(self.client.get(reverse("painel:agenda")).status_code, 403)

    def test_sem_login_vai_para_o_login(self):
        self.client.logout()
        resposta = self.client.get(reverse("painel:agenda"))
        self.assertEqual(resposta.status_code, 302)
        self.assertIn(reverse("contas:entrar"), resposta.url)

    def test_agenda_do_dia(self):
        services.agendar(paciente=self.paciente, profissional=self.prof, servico=self.servico, inicio=_aware(self.dia, time(9)))
        resposta = self.client.get(reverse("painel:agenda"), {"data": self.dia.isoformat()})
        self.assertContains(resposta, "João Melo")
        self.assertContains(resposta, "wa.me/5589999990000")

    def test_confirmar_e_pagar(self):
        c = services.agendar(paciente=self.paciente, profissional=self.prof, servico=self.servico, inicio=_aware(self.dia, time(9)))
        self.client.post(reverse("painel:acao", args=[c.pk, "confirmar"]))
        c.refresh_from_db()
        self.assertEqual(c.status, "confirmada")
        self.client.post(reverse("painel:pagamento", args=[c.pk]), {"valor": "150,00", "forma": "pix"})
        self.assertEqual(c.pagamentos.count(), 1)

    def test_acao_com_htmx_devolve_a_linha(self):
        c = services.agendar(paciente=self.paciente, profissional=self.prof, servico=self.servico, inicio=_aware(self.dia, time(9)))
        resposta = self.client.post(reverse("painel:acao", args=[c.pk, "confirmar"]), HTTP_HX_REQUEST="true")
        self.assertContains(resposta, f'id="consulta-{c.pk}"')
        self.assertContains(resposta, "Confirmada")

    def test_nova_consulta_pela_recepcao(self):
        resposta = self.client.post(reverse("painel:nova_consulta"), {
            "paciente": self.paciente.pk, "profissional": self.prof.pk, "servico": self.servico.pk,
            "data": self.dia.isoformat(), "horario": "10:00",
        })
        consulta = Consulta.objects.get()
        self.assertEqual(consulta.origem, "recepcao")
        self.assertEqual(consulta.criado_por, self.recepcao)
        self.assertEqual(resposta.status_code, 302)

    def test_encaixe_fora_da_grade(self):
        self.client.post(reverse("painel:nova_consulta"), {
            "paciente": self.paciente.pk, "profissional": self.prof.pk, "servico": self.servico.pk,
            "data": self.dia.isoformat(), "encaixe": "on", "hora_encaixe": "12:30",
        })
        self.assertTrue(Consulta.objects.get().encaixe)

    def test_busca_de_paciente(self):
        resposta = self.client.get(reverse("painel:buscar_pacientes"), {"q": "529982"})
        self.assertContains(resposta, "João Melo")

    def test_cadastrar_paciente(self):
        resposta = self.client.post(reverse("painel:paciente_novo"), {
            "nome": "Maria Dias", "cpf": "111.444.777-35", "data_nascimento": "1970-02-02", "sexo": "F",
            "telefone": "(89) 98888-7777",
        })
        maria = Paciente.objects.get(nome="Maria Dias")
        self.assertRedirects(resposta, reverse("painel:paciente", args=[maria.pk]))
