from django.test import TestCase
from django.urls import reverse

from apps.clinica.models import Especialidade

from .models import Orientacao, PerguntaFrequente


class InicioTests(TestCase):
    def test_pagina_inicial_abre(self):
        resposta = self.client.get(reverse("site_publico:inicio"))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Saúde Agora")

    def test_mostra_especialidades_do_banco(self):
        Especialidade.objects.create(nome="Cardiologia", descricao="Coração e pressão")
        resposta = self.client.get(reverse("site_publico:inicio"))
        self.assertContains(resposta, "Cardiologia")

    def test_secoes_vazias_nao_aparecem(self):
        resposta = self.client.get(reverse("site_publico:inicio"))
        self.assertNotContains(resposta, 'id="convenios"')
        self.assertNotContains(resposta, 'id="duvidas"')

    def test_mostra_perguntas_frequentes(self):
        PerguntaFrequente.objects.create(pergunta="Aceita convênio?", resposta="Sim.")
        resposta = self.client.get(reverse("site_publico:inicio"))
        self.assertContains(resposta, "Aceita convênio?")


class OrientacaoTests(TestCase):
    def test_pagina_da_orientacao(self):
        item = Orientacao.objects.create(titulo="Preparo para exame de sangue", resumo="Jejum e cuidados.", conteudo="Texto.")
        self.assertEqual(item.slug, "preparo-para-exame-de-sangue")
        self.assertEqual(self.client.get(item.get_absolute_url()).status_code, 200)
        self.assertEqual(self.client.get(reverse("site_publico:orientacoes")).status_code, 200)

    def test_orientacao_inativa_da_404(self):
        item = Orientacao.objects.create(titulo="Rascunho", resumo="x", conteudo="x", ativo=False)
        self.assertEqual(self.client.get(item.get_absolute_url()).status_code, 404)


class PaginasNovasTests(TestCase):
    def test_paginas_legais(self):
        self.assertContains(self.client.get(reverse("site_publico:privacidade")), "Política de privacidade")
        self.assertContains(self.client.get(reverse("site_publico:termos")), "Termos de uso")

    def test_perfil_do_profissional(self):
        from apps.contas.models import Usuario
        from apps.clinica.models import Profissional

        usuario = Usuario.objects.create_user("dr@teste.com", "Senha-forte-2026", nome="Dra. Teste", tipo="profissional")
        prof = Profissional.objects.create(usuario=usuario, registro="1111", bio="Apresentação de teste.")
        resposta = self.client.get(reverse("site_publico:profissional", args=[prof.pk]))
        self.assertContains(resposta, "Dra. Teste")
        self.assertContains(resposta, "Apresentação de teste.")
