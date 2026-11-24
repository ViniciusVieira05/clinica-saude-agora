from datetime import date

from django.test import TestCase
from django.urls import reverse

from apps.contas.models import Usuario
from apps.pacientes.models import Paciente


class ContaTests(TestCase):
    dados = {
        "nome": "Ana Souza", "cpf": "529.982.247-25", "data_nascimento": "1990-01-01",
        "telefone": "(89) 99999-9999", "email": "ana@teste.com",
        "senha1": "Senha-forte-2026", "senha2": "Senha-forte-2026", "aceite_termos": "on",
    }

    def test_criar_conta_cria_usuario_paciente_e_entra(self):
        resposta = self.client.post(reverse("contas:criar"), self.dados)
        self.assertRedirects(resposta, reverse("contas:minha_area"))
        usuario = Usuario.objects.get(email="ana@teste.com")
        self.assertEqual(usuario.paciente.cpf, "52998224725")
        self.assertIsNotNone(usuario.paciente.aceite_termos_em)
        self.assertEqual(int(self.client.session["_auth_user_id"]), usuario.pk)

    def test_liga_a_ficha_criada_pela_recepcao(self):
        ficha = Paciente.objects.create(nome="Ana Souza", cpf="52998224725", data_nascimento=date(1990, 1, 1), telefone="89988887777")
        self.client.post(reverse("contas:criar"), self.dados)
        ficha.refresh_from_db()
        self.assertIsNotNone(ficha.usuario)
        self.assertEqual(Paciente.objects.count(), 1)

    def test_nao_cria_duas_contas_com_o_mesmo_cpf(self):
        self.client.post(reverse("contas:criar"), self.dados)
        self.client.logout()
        outro = {**self.dados, "email": "outra@teste.com"}
        resposta = self.client.post(reverse("contas:criar"), outro)
        self.assertContains(resposta, "Já existe uma conta com este CPF")

    def test_exige_aceite_dos_termos(self):
        sem_aceite = {k: v for k, v in self.dados.items() if k != "aceite_termos"}
        resposta = self.client.post(reverse("contas:criar"), sem_aceite)
        self.assertContains(resposta, "É preciso aceitar")

    def test_entrar_com_email(self):
        Usuario.objects.create_user("ana@teste.com", "Senha-forte-2026", nome="Ana")
        resposta = self.client.post(reverse("contas:entrar"), {"username": "ana@teste.com", "password": "Senha-forte-2026"})
        self.assertRedirects(resposta, reverse("site_publico:inicio"), fetch_redirect_response=False)

    def test_nao_liga_ficha_com_data_de_nascimento_diferente(self):
        Paciente.objects.create(nome="Marcos Andrade", cpf="52998224725", data_nascimento=date(1975, 3, 3), telefone="89988887777")
        resposta = self.client.post(reverse("contas:criar"), self.dados)
        self.assertContains(resposta, "já está cadastrado na clínica com outros dados")
        self.assertFalse(Usuario.objects.filter(email="ana@teste.com").exists())

    def test_ao_ligar_a_ficha_o_nome_do_login_vira_o_da_ficha(self):
        Paciente.objects.create(nome="Ana Souza Lima", cpf="52998224725", data_nascimento=date(1990, 1, 1), telefone="89988887777")
        self.client.post(reverse("contas:criar"), self.dados)
        self.assertEqual(Usuario.objects.get(email="ana@teste.com").nome, "Ana Souza Lima")


class MinhaAreaTests(TestCase):
    def test_mostra_saudacao_e_atalhos(self):
        usuario = Usuario.objects.create_user("ze@teste.com", "Senha-forte-2026", nome="Zé Lima")
        Paciente.objects.create(usuario=usuario, nome="Zé Lima", cpf="11144477735", data_nascimento=date(1990, 1, 1), telefone="89999999999")
        self.client.force_login(usuario)
        resposta = self.client.get(reverse("contas:minha_area"))
        self.assertContains(resposta, "Olá, Zé.")
        self.assertContains(resposta, "Você não tem consultas marcadas")
