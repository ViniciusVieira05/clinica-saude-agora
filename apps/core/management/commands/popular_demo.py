"""Preenche o banco com dados fictícios para demonstração.

Uso:
    python manage.py popular_demo            # cria os dados (pode rodar de novo sem duplicar)
    python manage.py popular_demo --limpar   # apaga as consultas de demonstração antes

Só roda quando DEMO=True no .env, para nunca misturar com dados reais.
"""
import random
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from apps.agenda.models import HorarioAtendimento
from apps.agendamentos.models import Consulta
from apps.clinica.models import Especialidade, Profissional, Servico
from apps.contas.models import Usuario
from apps.financeiro.models import Pagamento
from apps.pacientes.models import Paciente
from apps.site_publico.models import Convenio, Orientacao, PerguntaFrequente

SENHA_DEMO = "Demo@2026"

ESPECIALIDADES = [
    ("Clínico geral", "Consultas de rotina, check-up e acompanhamento.", [("Consulta clínica", 30, "150.00"), ("Retorno", 20, "80.00")]),
    ("Cardiologia", "Coração, pressão alta e prevenção.", [("Consulta cardiológica", 40, "250.00"), ("Eletrocardiograma", 20, "90.00")]),
    ("Pediatria", "Cuidado com a saúde de bebês, crianças e adolescentes.", [("Consulta pediátrica", 30, "180.00")]),
    ("Odontologia", "Limpeza, avaliação e tratamentos odontológicos.", [("Avaliação odontológica", 30, "100.00"), ("Limpeza", 40, "150.00")]),
]

PROFISSIONAIS = [
    ("medico@demo.com", "Dr. Rafael Moura", "CRM", "4521", ["Clínico geral", "Cardiologia"],
     "Clínico geral e cardiologista, com 12 anos de experiência em prevenção e acompanhamento de pacientes crônicos."),
    ("pediatra@demo.com", "Dra. Helena Costa", "CRM", "6873", ["Pediatria"],
     "Pediatra dedicada ao acompanhamento do crescimento e desenvolvimento infantil."),
    ("dentista@demo.com", "Dr. Lucas Ribeiro", "CRO", "3190", ["Odontologia"],
     "Cirurgião-dentista com foco em prevenção, estética e reabilitação oral."),
]

NOMES = [
    "Ana Beatriz Lima", "Carlos Eduardo Rocha", "Fernanda Alves", "João Pedro Sousa", "Mariana Castro",
    "Paulo Henrique Dias", "Juliana Martins", "Ricardo Nunes", "Camila Ferreira", "Gabriel Teixeira",
    "Larissa Gomes", "Thiago Barbosa", "Patrícia Mendes", "Rafael Cardoso", "Beatriz Oliveira",
]


def gerar_cpf(semente):
    """CPF válido (fictício) a partir de um número."""
    base = [int(d) for d in str(100000000 + semente * 7919)[-9:]]
    for tamanho in (9, 10):
        soma = sum(d * (tamanho + 1 - i) for i, d in enumerate(base))
        base.append((soma * 10) % 11 % 10)
    return "".join(map(str, base))


class Command(BaseCommand):
    help = "Cria dados fictícios para a demonstração do sistema."

    def add_arguments(self, parser):
        parser.add_argument("--limpar", action="store_true", help="Apaga as consultas e pagamentos antes de criar de novo.")

    @transaction.atomic
    def handle(self, *args, **opcoes):
        if not getattr(settings, "DEMO", False):
            raise CommandError("Este comando só roda com DEMO=True no .env (ambiente de demonstração).")

        random.seed(42)
        if opcoes["limpar"]:
            Pagamento.objects.all().delete()
            Consulta.objects.all().delete()
            self.stdout.write("Consultas e pagamentos apagados.")

        servicos = self._clinica()
        profissionais = self._profissionais()
        pacientes = self._pacientes()
        self._usuarios_de_acesso(pacientes[0])
        self._site()
        criadas = self._consultas(profissionais, servicos, pacientes)

        self.stdout.write(self.style.SUCCESS(f"Demonstração pronta: {criadas} consultas criadas."))
        self.stdout.write("Logins de teste (senha para todos: %s):" % SENHA_DEMO)
        self.stdout.write("  Recepção:  recepcao@demo.com")
        self.stdout.write("  Paciente:  paciente@demo.com")
        self.stdout.write("  Médico:    medico@demo.com")

    # ---------------------------------------------------------------
    def _clinica(self):
        servicos = {}
        for nome, descricao, lista in ESPECIALIDADES:
            # Procura pelo slug para reaproveitar especialidades já cadastradas
            # (ex.: "Clínico Geral" e "Clínico geral" são a mesma).
            esp = Especialidade.objects.filter(slug=slugify(nome)).first()
            if esp is None:
                esp = Especialidade.objects.create(nome=nome, descricao=descricao)
            servicos[esp.nome] = []
            for serv_nome, duracao, preco in lista:
                serv = Servico.objects.filter(especialidade=esp, nome__iexact=serv_nome).first()
                if serv is None:
                    serv = Servico.objects.create(
                        especialidade=esp, nome=serv_nome, duracao_min=duracao, preco=Decimal(preco)
                    )
                servicos[esp.nome].append(serv)
        return servicos

    def _profissionais(self):
        lista = []
        for email, nome, conselho, registro, especialidades, bio in PROFISSIONAIS:
            usuario, criado = Usuario.objects.get_or_create(
                email=email, defaults={"nome": nome, "tipo": Usuario.Tipo.PROFISSIONAL}
            )
            if criado:
                usuario.set_password(SENHA_DEMO)
                usuario.save()
            prof, _ = Profissional.objects.get_or_create(
                usuario=usuario, defaults={"conselho": conselho, "registro": registro, "uf_registro": "PI", "bio": bio}
            )
            prof.especialidades.set(Especialidade.objects.filter(slug__in=[slugify(n) for n in especialidades]))
            for dia in range(5):  # segunda a sexta
                HorarioAtendimento.objects.get_or_create(
                    profissional=prof, dia_semana=dia,
                    defaults={"hora_inicio": time(8), "hora_fim": time(17),
                              "intervalo_inicio": time(12), "intervalo_fim": time(13, 30)},
                )
            HorarioAtendimento.objects.get_or_create(
                profissional=prof, dia_semana=5, defaults={"hora_inicio": time(8), "hora_fim": time(12)}
            )
            lista.append(prof)
        return lista

    def _pacientes(self):
        pacientes = []
        for i, nome in enumerate(NOMES):
            paciente, _ = Paciente.objects.get_or_create(
                cpf=gerar_cpf(i + 1),
                defaults={
                    "nome": nome,
                    "data_nascimento": datetime(1960 + (i * 3) % 50, (i % 12) + 1, (i % 27) + 1).date(),
                    "telefone": f"8999{(1000000 + i * 1371) % 10000000:07d}",
                    "email": f"paciente{i + 1}@exemplo.com",
                    "cidade": settings.CLINICA.get("cidade", ""),
                    "uf": "PI",
                },
            )
            pacientes.append(paciente)
        return pacientes

    def _usuarios_de_acesso(self, paciente_demo):
        recepcao, criado = Usuario.objects.get_or_create(
            email="recepcao@demo.com", defaults={"nome": "Recepção Demo", "tipo": Usuario.Tipo.RECEPCAO}
        )
        if criado:
            recepcao.set_password(SENHA_DEMO)
            recepcao.save()
        paciente_user, criado = Usuario.objects.get_or_create(
            email="paciente@demo.com", defaults={"nome": paciente_demo.nome, "tipo": Usuario.Tipo.PACIENTE}
        )
        if criado:
            paciente_user.set_password(SENHA_DEMO)
            paciente_user.save()
        if paciente_demo.usuario_id is None:
            paciente_demo.usuario = paciente_user
            paciente_demo.aceite_termos_em = timezone.now()
            paciente_demo.save()

    def _site(self):
        for i, nome in enumerate(["Unimed", "Bradesco Saúde", "SulAmérica", "Hapvida"]):
            Convenio.objects.get_or_create(nome=nome, defaults={"ordem": i})
        perguntas = [
            ("Vocês atendem convênio?", "Sim. Veja os convênios aceitos nesta página e confirme a cobertura do seu procedimento com a recepção."),
            ("Posso cancelar ou remarcar pelo site?", "Pode. Entre na sua conta, em Meus agendamentos, até 12 horas antes da consulta. Depois disso, fale com a recepção pelo WhatsApp."),
            ("Preciso chegar antes do horário?", "Recomendamos chegar 15 minutos antes, com documento com foto e exames anteriores, se tiver."),
            ("Quais as formas de pagamento?", "Pix, dinheiro, cartão de débito e de crédito."),
        ]
        for i, (pergunta, resposta) in enumerate(perguntas):
            PerguntaFrequente.objects.get_or_create(pergunta=pergunta, defaults={"resposta": resposta, "ordem": i})
        Orientacao.objects.get_or_create(
            titulo="Como se preparar para o exame de sangue",
            defaults={
                "resumo": "Jejum, hidratação e o que evitar nas horas antes da coleta.",
                "conteudo": "Para a maioria dos exames de sangue, o jejum recomendado é de 8 a 12 horas. "
                            "Beba água normalmente, que não quebra o jejum.\n\n"
                            "Evite bebidas alcoólicas e exercícios intensos nas 24 horas anteriores. "
                            "Se usa medicamentos de uso contínuo, pergunte ao seu médico se deve tomá-los antes da coleta.",
            },
        )
        Orientacao.objects.get_or_create(
            titulo="O que levar na primeira consulta",
            defaults={
                "resumo": "Documentos, exames e informações que ajudam o médico a te atender melhor.",
                "conteudo": "Leve um documento com foto e, se tiver, a carteirinha do convênio.\n\n"
                            "Traga exames recentes e a lista dos medicamentos que usa, com as doses. "
                            "Anote as dúvidas que quer tirar, para não esquecer na hora.",
            },
        )

    def _consultas(self, profissionais, servicos, pacientes):
        agora = timezone.localtime()
        hoje = agora.date()
        fuso = timezone.get_current_timezone()
        criadas = 0
        for deslocamento in range(-5, 8):
            data = hoje + timedelta(days=deslocamento)
            if data.weekday() == 6:
                continue
            for prof in profissionais:
                opcoes_servico = [s for e in prof.especialidades.all() for s in servicos.get(e.nome, [])]
                if not opcoes_servico:
                    continue
                horarios = [time(8), time(9), time(10), time(11), time(14), time(15), time(16)]
                if data.weekday() == 5:
                    horarios = [time(8), time(9), time(10)]
                for hora in random.sample(horarios, k=min(len(horarios), random.randint(2, 4))):
                    servico = random.choice(opcoes_servico)
                    inicio = timezone.make_aware(datetime.combine(data, hora), fuso)
                    fim = inicio + timedelta(minutes=servico.duracao_min)
                    paciente = random.choice(pacientes)
                    ocupado = Consulta.objects.filter(
                        inicio__lt=fim, fim__gt=inicio
                    ).exclude(status=Consulta.Status.CANCELADA).filter(
                        profissional=prof
                    ).exists() or Consulta.objects.filter(
                        paciente=paciente, inicio__lt=fim, fim__gt=inicio
                    ).exclude(status=Consulta.Status.CANCELADA).exists()
                    if ocupado:
                        continue
                    if inicio < agora:
                        status = random.choices(
                            [Consulta.Status.REALIZADA, Consulta.Status.FALTOU, Consulta.Status.CANCELADA],
                            weights=[8, 1, 1],
                        )[0]
                    else:
                        status = random.choice([Consulta.Status.AGENDADA, Consulta.Status.CONFIRMADA])
                    consulta = Consulta.objects.create(
                        paciente=paciente, profissional=prof, servico=servico, inicio=inicio, fim=fim,
                        status=status, preco=servico.preco,
                        origem=random.choice([Consulta.Origem.SITE, Consulta.Origem.RECEPCAO]),
                        cancelada_em=timezone.now() if status == Consulta.Status.CANCELADA else None,
                    )
                    if status == Consulta.Status.REALIZADA:
                        Pagamento.objects.create(
                            consulta=consulta, valor=servico.preco,
                            forma=random.choice([f for f, _ in Pagamento.Forma.choices]), pago_em=fim,
                        )
                    criadas += 1
        return criadas
