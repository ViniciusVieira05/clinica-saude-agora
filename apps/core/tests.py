from datetime import date

from django.test import TestCase

from apps.core.models import LogAuditoria
from apps.pacientes.models import Paciente


class AuditoriaTests(TestCase):
    def test_registra_criacao_e_alteracao(self):
        p = Paciente.objects.create(nome="Ana", cpf="52998224725", data_nascimento=date(1990, 1, 1), telefone="89999999999")
        self.assertTrue(LogAuditoria.objects.filter(acao="criar", objeto_id=str(p.pk)).exists())

        p.telefone = "89911112222"
        p.save()
        log = LogAuditoria.objects.filter(acao="alterar", objeto_id=str(p.pk)).get()
        self.assertEqual(log.dados_depois, {"telefone": "89911112222"})
        self.assertEqual(log.dados_antes, {"telefone": "89999999999"})

    def test_salvar_sem_mudanca_nao_gera_log(self):
        p = Paciente.objects.create(nome="Ana", cpf="52998224725", data_nascimento=date(1990, 1, 1), telefone="89999999999")
        p.save()
        self.assertFalse(LogAuditoria.objects.filter(acao="alterar").exists())
